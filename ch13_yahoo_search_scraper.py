#!/usr/bin/env python
"""
ch13_yahoo_search_scraper.py

Produce a feed from a Yahoo! web search.
"""
import sys
from scraperlib import Scraper, FeedEntryDict
from yahoo.search.webservices import WebSearch

YWS_APP_ID       = "hacking_rss"
YWS_SEARCH_QUERY = "Doctor Who"

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = YahooSearchScraper(YWS_APP_ID, YWS_SEARCH_QUERY)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class YahooSearchScraper(Scraper):
    """
    Generates feeds from lists of products from Yahoo! Web 
    Services queries.
    """
    FEED_META = {
        'feed.title'        : 'Yahoo! Search Results',
        'feed.link'         : 'http://www.yahoo.com',
        'feed.tagline'      : 'Search results from Yahoo.com',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }
    
    STATE_FN   = "yahoo_search_state"
    
    def __init__(self, app_id, search_query):
        """Initialize the Yahoo search scraper"""
        self.app_id       = app_id
        self.search_query = search_query

        self.FEED_META['feed.title'] = \
            'Yahoo! web search results for "%s"' % search_query

    def produce_entries(self):
        """
        Produce feed entries from Yahoo! product item data.
        """
        # Start off with an empty list for entries.
        entries = []

        # Create a new Yahoo! API web search
        search = WebSearch(self.app_id, query=self.search_query, results=50)

        # Execute the query and gather results.
        results = [ r for r in search.parse_results() ]

        # Sort the results in reverse-chronological order by
        # modification date
        results.sort(lambda a,b: \
            cmp(b['ModificationDate'], a['ModificationDate']))

        # Run through all fetched items, building entries
        for result in results:
            
            # Map the web search result data to feed entry properties
            entry = FeedEntryDict(date_fmt=self.date_fmt, init_dict={
                'title'    : result['Title'],
                'link'     : result['ClickUrl'],
                'summary'  : result['Summary'],
                'modified' : int(result['ModificationDate']),
                'issued'   : int(result['ModificationDate']),
            })

            # Append completed entry to list
            entries.append(entry)

        return entries
        
if __name__ == "__main__": main()
