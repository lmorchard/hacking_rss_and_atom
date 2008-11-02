#!/usr/bin/env python
"""
ch05_plucker_aggregator.py

Poll subscriptions, produce HTML summaries, wrap up as a plucker document.
"""

import sys, time
from agglib import *
import PyPlucker.Spider

HTML_FN       = "plucker-aggregator-%s.html" % time.strftime("%Y%m%d-%H%M%S")
FEEDS_FN      = "plucker_feeds.txt"
FEED_DB_FN    = "plucker_feeds_db"
ENTRY_DB_FN   = "plucker_entry_seen_db"

PLUCKER_DIR   = "."
PLUCKER_TITLE = "%s News" % time.strftime("%Y%m%d-%H%M%S")
PLUCKER_FN    = "plucker-%s" % time.strftime("%Y%m%d-%H%M%S")
PLUCKER_BPP   = "0"
PLUCKER_DEPTH = "1"

def main(): 
    """
    Poll subscribed feeds and produce aggregator page.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    if len(entries) > 0:
        out_fn = HTML_FN
        writeAggregatorPage(entries, out_fn, DATE_HDR_TMPL, FEED_HDR_TMPL, 
            ENTRY_TMPL, PAGE_TMPL)
        buildPluckerDocument(PLUCKER_DIR, PLUCKER_FN, PLUCKER_TITLE, 
            PLUCKER_DEPTH, PLUCKER_BPP, HTML_FN)
    
    closeDBs(feed_db, entry_db)

def buildPluckerDocument(pdir, pfn, ptitle, pdepth, pbpp, html_fn):
    """
    Given some Plucker settings and an HTML file, attempt to build a 
    Plucker document.
    """
    PyPlucker.Spider.realmain(None, argv=[
        sys.argv[0],
        '-P', pdir,
        '-f', pfn,
        '-H', html_fn,
        '-N', ptitle,
        '-M', pdepth,
        '--bpp', pbpp,
        '--title=%s' % ptitle,
    ])

# Presentation templates for output follow:

DATE_HDR_TMPL = """
    <h2>%s</h1>
"""

FEED_HDR_TMPL = """
    <h3><a href="%(feed.link)s">%(feed.title)s</a></h2>
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
    <head>
    </head>
    <body>
        <h1>Feed aggregator #1</h1>
        %s
    </body>
</html>
"""

if __name__ == "__main__": main()
