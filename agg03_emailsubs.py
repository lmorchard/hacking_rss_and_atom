#!/usr/bin/env python
"""
agg03_pollsubs.py

Poll subscriptions and email an aggregate HTML page.
"""
import sys, time, feedparser, shelve, md5, time

from agglib import UNICODE_ENC, openDBs, closeDBs
from agglib import getNewFeedEntries, writeAggregatorPage

import smtplib 
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

FROM_ADDR   = "you@your-address.com"
TO_ADDR     = "you@your-address.com"
SUBJECT     = "New news for you!"
SMTP_HOST   = "localhost"

FEEDS_FN    = "feeds.txt"
HTML_FN     = "aggregator-%s.html"

FEED_DB_FN  = "feeds_db"
ENTRY_DB_FN = "entry_seen_db"

def main(): 
    """
    Poll subscribed feeds and produce aggregator page.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    if len(entries) > 0:
        out_fn = HTML_FN % time.strftime("%Y%m%d-%H%M%S")
        writeAggregatorPage(entries, out_fn, DATE_HDR_TMPL, FEED_HDR_TMPL, 
            ENTRY_TMPL, PAGE_TMPL)
        emailAggregatorPage(FROM_ADDR, TO_ADDR, SUBJECT, SMTP_HOST, out_fn)
    
    closeDBs(feed_db, entry_db)

def emailAggregatorPage(from_addr, to_addr, subj, smtp_host, out_fn):
    """
    Read in the HTML page produced by an aggregator run, construct a
    MIME-Multipart email message with the HTML attached, and send it off
    with the given from, to, and subject headers using the specified
    SMTP mail server.
    """
    # Begin building the email message.
    msg = MIMEMultipart()
    msg['To']      = to_addr
    msg['From']    = from_addr
    msg['Subject'] = subj
    msg.preamble   = "You need a MIME-aware mail reader.\n"
    msg.epilogue   = ""

    # Generate a plain text alternative part.
    plain_text = """
    This email contains entries from your subscribed feeds in HTML.
    """
    part = MIMEText(plain_text, "plain", UNICODE_ENC)
    msg.attach(part)

    # Generate the aggregate HTML page, read in the HTML data, attach it
    # as another part of the email message.
    html_text = open(out_fn).read()
    part = MIMEText(html_text, "html", UNICODE_ENC)
    msg.attach(part)

    # Finally, send the whole thing off as an email message.
    print "Sending email '%s' to '%s'" % (subj, to_addr)
    s = smtplib.SMTP(smtp_host)
    s.sendmail(from_addr, to_addr, msg.as_string())
    s.close()

# Presentation templates for output follow:

DATE_HDR_TMPL = """
    <h1 class="dateheader">%s</h1>
"""

FEED_HDR_TMPL = """
    <h2 class="feedheader"><a href="%(feed.link)s">%(feed.title)s</a></h2>
"""

ENTRY_TMPL = """
    <div class="feedentry">
        <div class="entryheader">
            <span class="entrytime">%(time)s</span>: 
            <a class="entrylink" href="%(entry.link)s">%(entry.title)s</a>
        </div>
        <div class="entrysummary">
            %(entry.summary)s
            <hr>
            %(content)s
        </div>
    </div>
"""

PAGE_TMPL = """
<html>
    <body>
        <h1 class="pageheader">Feed aggregator #1</h1>
        %s
    </body>
</html>
"""

if __name__ == "__main__": main()
