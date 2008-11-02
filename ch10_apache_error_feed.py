#!/usr/bin/env python
"""
ch10_apache_error_feed.py

Provide a periodic tail of the Apache error log.
"""
import sys, os, re, shelve
from xml.sax.saxutils import escape
from scraperlib import FeedEntryDict
from monitorfeedlib import LogBufferFeed
from ch10_bookmark_tailgrep import bookmark_tailgrep

SITE_NAME    = "0xDECAFBAD"
ERROR_LOG    = "www/www.decafbad.com/logs/error.log" 
FEED_NAME_FN = "www/www.decafbad.com/docs/private-feeds/errors.%s"
FEED_DIR     = "error_feed"

def main():
    """
    Report new errors found in Apache logs.
    """
    # Construct the feed generator
    f = LogBufferFeed(FEED_DIR)
    f.MAX_AGE = 24 * 60 * 60 # 1 day
    f.FEED_META['feed.title']   = '%s Apache Errors' % SITE_NAME
    f.FEED_META['feed.tagline'] = \
        'New errors from Apache on %s' % SITE_NAME
    
    # If there were new referrers found, insert a new entry.
    new_lines = bookmark_tailgrep(ERROR_LOG, 
                                  max_initial_lines=3000)

    if len(new_lines) > 0:
        # Construct and append a new entry
        esc_lines = [escape(x) for x in new_lines]
        entry = FeedEntryDict({
            'title'   : '%s new lines of errors' % len(new_lines),
            'link'    : '',
            'summary' : """
                <div style="font-family:monospace">
                    %s
                </div>
            """ % "<br />\n".join(esc_lines)
        })
        f.append_entry(entry)

    # Output the current feed entries as both RSS and Atom
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())

if __name__ == '__main__': main()
