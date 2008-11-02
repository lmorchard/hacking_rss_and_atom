#!/usr/bin/env python
"""
agg05_im_subs.py

Poll subscriptions and send a series of IMs with the latest headlines
"""
import time
from agglib import openDBs, closeDBs, getNewFeedEntries
from imconn import AIMConnection, JabberConnection

IM_CLASS   = AIMConnection
IM_TO      = "your_name"
IM_USER    = "your_name"
IM_PASSWD  = "your_password"

IM_CHUNK   = 7

FEED_HDR_TMPL = """\n<a href="%(feed.link)s"><u>%(feed.title)s</u></a>\n\n"""
ENTRY_TMPL    = """    * <a href="%(entry.link)s">%(entry.title)s</a>\n"""
MSG_TMPL      = "%s"

#IM_CLASS   = JabberConnection
#IM_TO      = "your_name@jabber.org"
#IM_USER    = "your_name@jabber.org"
#IM_PASSWD  = "your_password"

#FEED_HDR_TMPL = """\n%(feed.title)s - %(feed.link)s\n\n"""
#ENTRY_TMPL    = """    * %(entry.title)s - %(entry.link)s\n\n"""
#MSG_TMPL      = "%s"

FEEDS_FN    = "feeds.txt"

FEED_DB_FN  = "feeds_db"
ENTRY_DB_FN = "entry_seen_db"

def main(): 
    """
    Poll subscribed feeds and send off IMs
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    # Create a new IM connection.
    conn = IM_CLASS(IM_USER, IM_PASSWD)
    conn.connect()
    
    # Read in the subscriptions
    feeds = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    # Iterate through subscribed feeds.
    for feed in feeds:
        # Get new entries for the current feed and send them off
        entries = getNewFeedEntries([feed], feed_db, entry_db)
        if len(entries) > 0:
            sendEntriesViaIM(conn, IM_TO, entries, IM_CHUNK, 
                    FEED_HDR_TMPL, ENTRY_TMPL, MSG_TMPL)
    
    closeDBs(feed_db, entry_db)

def sendEntriesViaIM(conn, to_nick, entries, im_chunk, feed_hdr_tmpl,
        entry_tmpl, msg_tmpl):
    """
    Given an IM connection, a destination name, and a list of entries,
    send off a series of IMs containing entries rendered via template.
    """
    out, curr_feed, entry_cnt = [], None, 0
    for entry in entries:

        # If there's a change in current feed, note it and append a 
        # feed header onto the message.
        if entry.feed.title != curr_feed:
            curr_feed = entry.feed.title
            out.append(feed_hdr_tmpl % entry)

        # Append the current entry to the outgoing message
        out.append(entry_tmpl % entry)

        # Keep count of entries.  Every IM_CHUNK worth, fire off the
        # accumulated message content as an IM and clear the current 
        # feed title to force a new header in the next batch.
        entry_cnt += 1
        if (entry_cnt % im_chunk) == 0:
            sendIMwithTemplate(conn, to_nick, out, msg_tmpl)
            out, curr_feed = [], None

    # Flush out any remaining content.
    if len(out) > 0:
        sendIMwithTemplate(conn, to_nick, out, msg_tmpl)

def sendIMwithTemplate(conn, to_nick, out, msg_tmpl):
    """
    Given an IM bot, a destination name, and a list of content, render
    the message template and send off the IM.
    """
    try:
        msg_text = msg_tmpl % "".join(out)
        conn.sendIM(to_nick, msg_text)
        time.sleep(4)
    except KeyboardInterrupt:
        raise
    except Exception, e:
        print "\tProblem sending IM: %s" % e

if __name__ == "__main__": main()
