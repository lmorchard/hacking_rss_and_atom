#!/usr/bin/env python
"""
agg04_emailsubs.py

Poll subscriptions and email each new entry as a separate message.
"""
import sys, time, feedparser, shelve, md5, time

from agglib import UNICODE_ENC, openDBs, closeDBs
from agglib import getNewFeedEntries, writeAggregatorPage

import smtplib 
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

FROM_ADDR   = "you@your-address.com"
TO_ADDR     = "you@your-address.com"
SUBJECT     = "[agg04] %(feed.title)s :: %(entry.title)s"
SMTP_HOST   = "localhost"

FEEDS_FN    = "feeds.txt"
UNICODE_ENC = "utf-8"

FEED_DB_FN  = "feeds_db"
ENTRY_DB_FN = "entry_seen_db"

def main(): 
    """
    Poll subscribed feeds and email out entries.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    if len(entries) > 0:
        emailEntries(FROM_ADDR, TO_ADDR, SUBJECT, SMTP_HOST, entries)
    
    closeDBs(feed_db, entry_db)

def emailEntries(from_addr, to_addr, subj, smtp_host, entries):
    """
    Given a from address, to address, a subject template, SMTP host,
    and a list of entries, construct an email message via template for
    each entry and send it off using the given header values.
    """
    for entry in entries:
        
        # Build a subject line for the current feed entry.
        curr_subj = subj % entry
        
        # Begin building the email message.
        msg = MIMEMultipart()
        msg['To']      = to_addr
        msg['From']    = from_addr
        msg['Subject'] = curr_subj
        msg.preamble   = "You would not see this in a MIME-aware mail reader.\n"
        msg.epilogue   = ""

        # Generate a plain text alternative part.
        plain_text = """
        This email contains entries from your subscribed feeds in HTML.
        """
        part = MIMEText(plain_text, "plain", UNICODE_ENC)
        msg.attach(part)

        # Generate the aggregate HTML page, read in the HTML data, attach it
        # as another part of the email message.
        out = []
        out.append(FEED_HDR_TMPL % entry)
        out.append(ENTRY_TMPL % entry)
        html_text = PAGE_TMPL % "".join(out)
        part = MIMEText(html_text, "html", UNICODE_ENC)
        msg.attach(part)

        # Finally, send the whole thing off as an email message.
        print "Sending email '%s' to '%s'" % (curr_subj, to_addr)
        s = smtplib.SMTP(smtp_host)
        s.sendmail(from_addr, to_addr, msg.as_string())
        s.close()

# Presentation templates for output follow:

FEED_HDR_TMPL = """
    <h2><a href="%(feed.link)s">%(feed.title)s</a></h2>
"""

ENTRY_TMPL = """
    <div>
        <div>
            <span>%(time)s</span>: 
            <a href="%(entry.link)s">%(entry.title)s</a>
        </div>
        <div>
            %(entry.summary)s
            <hr>
            %(content)s
        </div>
    </div>
"""

PAGE_TMPL = """
<html>
    <body>
        %s
    </body>
</html>
"""

if __name__ == "__main__": main()
