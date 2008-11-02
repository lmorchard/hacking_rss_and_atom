"""
mailfeedlib

Utilities for generating feeds from mail messages.
"""
import sys, time, shelve, md5, re
from urllib import quote
from urlparse import urlparse
import email, email.Utils
from xml.sax.saxutils import escape
from scraperlib import FeedEntryDict, Scraper

import poplib

class POP3Client:
    """
    Generic interface to fetch messages from a POP3 mailbox.
    """
    def __init__(self, host='localhost', port=110, user=None, passwd=None):
        """Initialize POP3 connection details."""
        self.host   = host
        self.port   = port
        self.user   = user
        self.passwd = passwd
    
    def fetch_messages(self, max_messages=15):
        """
        Fetch messages up to the maximum, return email.Message objects.
        """
        # Connect to the POP3 mailbox
        mailbox = poplib.POP3(self.host, self.port)
        mailbox.user(self.user)
        mailbox.pass_(self.passwd)

        # Look up messages, establish a window for fetching
        nums = range(len(mailbox.list()[1]))
        end_pos   = len(nums)
        start_pos = max(0, end_pos - max_messages)
        
        # Fetch and accumulate Messages
        msgs = []
        for i in nums[start_pos:end_pos]:
            try:
                msg_txt = "\n".join(mailbox.retr(i+1)[1])
                msg     = email.message_from_string(msg_txt)
                msgs.append(msg)
            except KeyboardInterrupt:
                raise
            except:
                pass

        # Log out of mailbox
        mailbox.quit()

        return msgs

import imaplib

class IMAP4Client:
    """
    Generic interface to fetch messages from a IMAP4 mailbox.
    """
    def __init__(self, host='localhost', port=110, user=None, passwd=None):
        """Initialize IMAP4 connection details."""
        self.host   = host
        self.port   = port
        self.user   = user
        self.passwd = passwd

    def fetch_messages(self, max_messages=15):
        """
        Fetch messages up to the maximum, return email.Message objects.
        """
        # Connect to the IMAP4 mailbox
        mailbox = imaplib.IMAP4(self.host, int(self.port))
        mailbox.login(self.user, self.passwd)
        mailbox.select()
        
        # Look up undeleted messages, establish a window for fetching
        nums = mailbox.search(None, "UNDELETED")[1][0].split()
        end_pos   = len(nums)
        start_pos = max(0, end_pos - max_messages)
        
        # Fetch and accumulate Messages
        msgs = []
        for i in nums[start_pos:end_pos]:
            try:
                msg_txt = mailbox.fetch(str(i), "RFC822")[1][0][1]
                msg     = email.message_from_string(msg_txt)
                msgs.append(msg)
            except KeyboardInterrupt:
                raise
            except:
                pass
            
        # Log out of mailbox
        mailbox.close()
        mailbox.logout()

        return msgs

class MailScraper(Scraper):
    """
    Use an email client to download messages on which to base a feed.
    """
    TAG_DOMAIN  = "mail.example.com"
    STATE_FN    = "mail_scraper_state"
    
    ATOM_ENTRY_TMPL = """
        <entry>
            <title>%(entry.title)s</title>
            <author>
                <name>%(entry.author.name)s</name>
            </author>
            <link rel="alternate" type="text/html"
                  href="%(entry.link)s" />
            <issued>%(entry.issued)s</issued>
            <modified>%(entry.modified)s</modified>
            <id>%(entry.id)s</id>
            <summary type="text/html" 
                     mode="escaped">%(entry.summary)s</summary>
        </entry>
    """
    
    def __init__(self, client, max_messages=15):
        """Initialize with a given mail client."""
        self.client = client
        self.max_messages = max_messages

    def produce_entries(self):
        """
        Fetch messages using email client, return a list of entries.
        """
        msgs = self.client.fetch_messages(max_messages=self.max_messages)
        filtered_msgs = self.filter_messages(msgs)
        return self.entries_from_messages(filtered_msgs)
            
    def filter_messages(self, msgs):
        """Return filtered list of messages for inclusion in feed."""
        return msgs

    def entries_from_messages(self, msgs):
        """
        Given a list of email.Message, attempt to build a list 
        of FeedEntryDict objects
        """
        entries = []
        
        for msg in msgs:
            
            entry = FeedEntryDict(date_fmt = self.date_fmt)
            
            # Set the 'dummy' link for the entry from feed.link
            entry['link']  = self.FEED_META['feed.link']
            
            # Use message Subject for entry title.
            entry['title'] = msg.get('Subject', '(Untitled)')

            # Use From header for entry author email.
            entry['author.name'] = msg['From']
            
            # Convert message Date into seconds, use for modified 
            # and issued
            msg_time_raw = email.Utils.parsedate(msg['Date'])
            msg_time     = time.mktime(msg_time_raw)
            entry.data['modified'] = entry.data['issued'] = msg_time
            
            # Get a GUID for this entry.
            entry['id']      = self.build_guid_for_message(msg, entry)
            
            # Summarize the email for the entry.
            entry['summary'] = self.extract_summary_from_message(msg)
             
            # Stuff the new entry into the running list.
            entries.append(entry)

        # Finally, return what was accumulated
        return entries

    def build_guid_for_message(self, msg, entry):
        """
        Build an entry GUID from message ID or hash.
        """
        # Try getting the Message-ID, construct an MD5 hash 
        # if unavailable.
        if msg.has_key('Message-ID'):
            msg_id = msg['Message-ID']
        else:
            m = md5.md5()
            m.update(entry.data['title'])
            m.update(entry.data['summary'])
            msg_id = m.hexdigest()

        # Build an entry GUID from message ID or hash.
        entry_time = entry.data['modified']
        ymd = time.strftime("%Y-%m-%d", time.gmtime(entry_time))
        id_quote = quote(msg_id) 
        return "tag:%s,%s:%s" % (self.TAG_DOMAIN, ymd, id_quote)

    def extract_summary_from_message(self, msg):
        """
        Walk through all the message parts, collecting content
        for entry summary.
        """
        body_segs = []
        parts = [ m for m in msg.walk() if m.get_payload(decode=True) ]
        for part in parts:
                
            # Grab message type, character encoding, and payload
            content_type = part.get_content_type()
            charset      = part.get_content_charset('us-ascii')
            payload      = part.get_payload(decode=True)

            # Sometimes, parts marked as ISO-8859-1 are really CP1252.
            # see: http://manatee.mojam.com/~skip/python/decodeh.py
            if charset == 'iso-8859-1' and \
                    re.search(r"[\x80-\x9f]", payload) is not None:
                charset = 'cp1252'

            # Only handle text parts here.
            if content_type.startswith('text/'):
                
                # Decode the email payload into Unicode, wimp out on errors.
                try:
                    body = payload.decode(charset, 'replace')
                except Exception, e:
                    body = "[ ENCODING ERROR: %s ]" % e
                
                # Include this text part wrapped in <pre> tags and escaped 
                if content_type == 'text/plain':
                    body_segs.append(u"<pre>\n%s</pre>" % escape(body))
            
            return "\n<hr />\n".join(body_segs)
    
