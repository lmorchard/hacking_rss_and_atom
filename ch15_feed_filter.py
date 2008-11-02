#!/usr/bin/env python
"""
ch15_feed_filter.py

Build a new feed out of entries filtered from a source feed.
"""
import sys, re, feedparser
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries

FEED_NAME_FN = "www/www.decafbad.com/docs/private-feeds/filtered.%s"
FEED_URI     = "http://del.icio.us/rss/deusx/webdev"
FILTER_RE    = {
    'category' : '.*python.*',
}

def main():
    """
    Perform a test run of the FeedFilter using defaults.
    """
    # Build the feed filter.
    f = FeedFilter(FEED_URI, FILTER_RE)
    f.STATE_FN = 'filter_state'
    
    # Output the feed as both RSS and Atom.
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())
    
class FeedFilter(Scraper):
    """
    Filter feed entries using a regex map.
    """
    def __init__(self, feed_uri, filter_re):
        """Initialize with the feed URI for parsing."""
        # Stow the feed URI and cache
        self.feed_uri   = feed_uri

        # Pre-compile all regexes
        self.filter_re = {}
        for k,v in filter_re.items():
            self.filter_re[k] = re.compile(v, 
                re.DOTALL | re.MULTILINE | re.IGNORECASE)

    def produce_entries(self):
        """
        Filter entries from a feed using the regex map, use the
        feed normalizer to produce FeedEntryDict objects.
        """
        # Use the cache to get the feed for filtering.
        feed_data = feedparser.parse(self.feed_uri)

        # Build the output feed's normalized metadata
        self.FEED_META = normalize_feed_meta(feed_data, self.date_fmt)
        
        # Now, apply the regex map to filter each incoming entry.
        entries_filtered = []
        for entry in feed_data.entries:
            # Initially assume the entry is okay for inclusion.
            ok_include = True
            
            # Iterate through each entry key and regex pair.
            for k,r in self.filter_re.items():
                # The first time a field of the entry fails to match
                # the regex map criteria, reject it for inclusion.
                if not (entry.has_key(k) and r.match(entry[k])):
                    ok_include = False
                    break
            
            # Finally, if the entry passes all the tests, include it.
            if ok_include: entries_filtered.append(entry)
                    
        # Normalize all the filtered entries
        entries = normalize_entries(entries_filtered)
        for entry in entries:
             entry.date_fmt = self.date_fmt

        return entries
        
if __name__=='__main__': main()
