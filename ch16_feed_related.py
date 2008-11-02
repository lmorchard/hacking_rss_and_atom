#!/usr/bin/env python
"""
ch16_feed_related.py

Insert related links into a normalized feed.
"""
import sys, urllib, feedparser, xmltramp
from xml.sax import SAXParseException
from httpcache import HTTPCache
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries

FEED_URL = 'http://www.decafbad.com/blog/index.xml' 

def main():
    """
    Use the FeedRelator on a given feed.
    """
    feed_url = ( len(sys.argv) > 2 ) and sys.argv[2] or FEED_URL

    f = FeedRelator(feed_url)
    f.STATE_FN = 'link_related_state'
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print f.scrape_rss()
    else:
        print f.scrape_atom()
    
class FeedRelator(Scraper):
    """
    Insert related links found via Technorati search into a
    normalized feed.
    """
    
    TECHNORATI_KEY  = open("technorati-key.txt", "r").read().strip()
    
    SEARCH_URL_TMPL = \
        "http://api.technorati.com/search?key=%s&limit=5&query=%s"

    INSERT_TMPL = """
        <div style="border: 1px solid #888; padding: 12px;">
            <b><u>Further reading:</u></b><br />
            <ul>
            %s
            </ul>
        </div>
    """
    INSERT_ITEM_TMPL = """
        <li>
            [<a href="%(weblog.url)s">%(weblog.name)s</a>]
            <a href="%(permalink)s">%(title)s</a>
        </li>
    """
    
    def __init__(self, main_feed):
        """Initialize with the feed URI for parsing."""
        self.main_feed = main_feed

    def produce_entries(self):
        """
        Use FeedNormalizer to get feed entries, then merge
        the lists together.
        """
        # Grab and parse the feed
        feed = feedparser.parse(HTTPCache(self.main_feed).content())
        
        # Normalize feed meta data
        self.FEED_META = normalize_feed_meta(feed, self.date_fmt)
        self.FEED_META['feed.title'] += ' (with related links)'

        # Normalize entries from the feed
        entries = normalize_entries(feed.entries)

        # Run through all the normalized entries...
        for e in entries:
            
            # Perform a search on the entry title, extract the items
            result = self.technorati_search(e['title'])
            items  = [ x for x in result if x._name == 'item' ]
            
            # Use each search result item to populate the templates.
            insert_items = [ self.INSERT_ITEM_TMPL % {
                'weblog.name' : i.weblog.name,
                'weblog.url'  : i.weblog.url,
                'title'       : i.title,
                'permalink'   : i.permalink
            } for i in items ]
            insert_out = self.INSERT_TMPL % '\n'.join(insert_items)

            # Append the rendered search results onto the entry summary.
            e.data['summary'] += insert_out.decode('utf-8', 'ignore')
            
        return entries

    def technorati_search(self, query):
        """
        Given a query string, perform a Technorati search.
        """
        # Construct a Technorati search URL and fetch it.
        url  = self.SEARCH_URL_TMPL % \
               ( self.TECHNORATI_KEY, urllib.quote_plus(query) )
        data = HTTPCache(url).content()

        # HACK: I get occasional encoding issues with Technorati, so
        # here's an ugly hack that seems to make things work anyway.
        try:
            return xmltramp.parse(data).document
        except SAXParseException:
            data = data.decode('ascii', 'ignore')
            return xmltramp.parse(data).document

if __name__=='__main__': main()
