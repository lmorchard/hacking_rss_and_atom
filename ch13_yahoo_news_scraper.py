#!/usr/bin/env python
"""
ch13_yahoo_news_scraper.py

Produce a feed from a Yahoo! web search.
"""
import sys
from scraperlib import Scraper, FeedEntryDict
from yahoo.search.webservices import NewsSearch

YWS_APP_ID       = "hacking_rss"
YWS_SEARCH_QUERY = "syndication feeds"

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = YahooNewsScraper(YWS_APP_ID, YWS_SEARCH_QUERY)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class YahooNewsScraper(Scraper):
    """
    Generates feeds from lists of products from Yahoo! Web 
    Services queries.
    """
    FEED_META = {
        'feed.title'        : 'Yahoo! News Search Results',
        'feed.link'         : 'http://www.yahoo.com',
        'feed.tagline'      : 'Search results from Yahoo.com',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }
    
    STATE_FN   = "yahoo_search_state"
    
    ATOM_ENTRY_TMPL = """
        <entry>
            <title>%(entry.title)s</title>
            <author>
                <name>%(entry.author.name)s</name>
                <link>%(entry.author.link)s</link>
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
    
    def __init__(self, app_id, search_query):
        """Initialize the Yahoo search scraper"""
        self.app_id       = app_id
        self.search_query = search_query

        self.FEED_META['feed.title'] = \
            'Yahoo! news search results for "%s"' % search_query

    def produce_entries(self):
        """
        Produce feed entries from Yahoo! product item data.
        """
        # Start off with an empty list for entries.
        entries = []

        # Create a new Yahoo! API web search
        search = NewsSearch(self.app_id, query=self.search_query,
                            sort='date', results=50)
        
        # Run through all fetched items, building entries
        for result in search.parse_results():
            
            # Map the web search result data to feed entry properties
            entry = FeedEntryDict(date_fmt=self.date_fmt, init_dict={
                'title'       : '[%s] %s' % \
                    (result['NewsSource'], result['Title']),
                'link'        : result['ClickUrl'],
                'summary'     : result['Summary'],
                'author.name' : result['NewsSource'],
                'author.link' : result['NewsSourceUrl'],
                'modified'    : int(result['ModificationDate']),
                'issued'      : int(result['PublishDate']),
            })

            # Append completed entry to list
            entries.append(entry)

        return entries
        
if __name__ == "__main__": main()
