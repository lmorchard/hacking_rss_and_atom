#!/usr/bin/env python
"""
ch16_feed_merger.py

Combine many feeds into a single normalized feed.
"""
import sys, feedparser
from httpcache import HTTPCache
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_entries

def main():
    """
    merge a handful of link feeds into one mega link feed.
    """
    feeds = [
        'http://blogdex.net/xml/index.asp',
        'http://dev.upian.com/hotlinks/rss.php?n=1',
        'http://del.icio.us/rss/',
        'http://www.daypop.com/top/rss.xml',
        'http://digg.com/rss/index.xml'
    ]

    f = FeedMerger(feeds)
    f.FEED_META['feed.title'] = "Merged link feed"
    f.STATE_FN = 'link_merger_state'
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print f.scrape_rss()
    else:
        print f.scrape_atom()
    
class FeedMerger(Scraper):
    """
    Merge several feeds into a single normalized feed.
    """
    INCLUDE_TITLE = True
    
    def __init__(self, feed_uris):
        """Initialize with the feed URI for parsing."""
        self.feed_uris = feed_uris

    def produce_entries(self):
        """
        Use FeedNormalizer to get feed entries, then merge
        the lists together.
        """
        entries = []
        
        # Iterate and gather normalized entries for each feed.
        for feed_uri in self.feed_uris:
            
            # Grab and parse the feed
            feed_data = feedparser.parse(HTTPCache(feed_uri).content())
            
            # Append the list of normalized entries onto merged list.
            curr_entries = normalize_entries(feed_data.entries)
            for e in curr_entries:
                if self.INCLUDE_TITLE:
                    e['title'] = "["+ feed_data.feed.title + "] " + \
                                 e.data['title']
            entries.extend(curr_entries)
        
        return entries

if __name__=='__main__': main()

