#!/usr/bin/env python
"""
ch13_google_search_scraper.py

Produce a feed from a Google web search.
"""
import sys
from scraperlib import Scraper, FeedEntryDict
#from pygoogle import google
import google

GOOGLE_LICENSE_KEY  = "XXXXXXXXXXXXXXXXXXXX"

import julian

tdy = julian.now()
yst = tdy - 1
GOOGLE_SEARCH_QUERY = '"Doctor Who" daterange:%s-%s' % (yst, tdy)

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = GoogleSearchScraper(GOOGLE_LICENSE_KEY, GOOGLE_SEARCH_QUERY)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class GoogleSearchScraper(Scraper):
    """
    Generates feeds from lists of products from Google Web 
    Services queries.
    """
    FEED_META = {
        'feed.title'        : 'Google Search Results',
        'feed.link'         : 'http://www.google.com',
        'feed.tagline'      : 'Search results from Google.com',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }
    
    STATE_FN   = "google_search_state"
    
    def __init__(self, license_key, search_query):
        """Initialize the Google search scraper"""
        self.license_key  = license_key
        self.search_query = search_query

        self.FEED_META['feed.title'] = \
            'Google web search results for "%s"' % search_query

    def produce_entries(self):
        """
        Produce feed entries from Google product item data.
        """
        # Start off with an empty list for entries.
        entries = []

        # Execute the Google search
        data = google.doGoogleSearch(self.search_query, 
                license_key=self.license_key)
        
        # Run through all fetched items, building entries
        for result in data.results:
            
            # Map the web search result data to feed entry properties
            entry = FeedEntryDict(date_fmt=self.date_fmt, init_dict={
                'title'    : result.directoryTitle or '(untitled)',
                'link'     : result.URL,
                'summary'  : result.snippet,
            })

            # Append completed entry to list
            entries.append(entry)

        return entries
        
if __name__ == "__main__": main()
