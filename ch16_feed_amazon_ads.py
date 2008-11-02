#!/usr/bin/env python
"""
ch16_feed_amazon_ads.py

Insert Amazon links into a normalized feed.
"""
import sys, urllib, feedparser, xmltramp
from xml.sax import SAXParseException
from httpcache import HTTPCache
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries

FEED_URL = 'http://www.decafbad.com/blog/atom.xml' 

def main():
    """
    Use the AmazonAdFeed on a given feed.
    """
    feed_url = ( len(sys.argv) > 2 ) and sys.argv[2] or FEED_URL

    f = AmazonAdFeed(feed_url)
    f.STATE_FN = 'link_amazon_ads_state'
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print f.scrape_rss()
    else:
        print f.scrape_atom()
    
class AmazonAdFeed(Scraper):
    """
    Insert amazon_ads links found via Technorati search into a
    normalized feed.
    """
    AMAZON_KEY    = open("amazon-key.txt", "r").read().strip()
    ASSOCIATE_TAG = '0xdecafbad-20'
    MAX_ITEMS     = 3
    
    INSERT_TMPL = """
        <div style="border: 1px solid #888; padding: 12px;">
            <b><u>Possibly Related Amazon Items:</u></b><br />
            <ul>
            %s
            </ul>
        </div>
    """
    INSERT_ITEM_TMPL = """
        <li>
            <img src="%(img)s" align="middle" style="padding: 5px;" />
            <a href="%(url)s">%(title)s</a>
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
        self.FEED_META['feed.title'] += ' (with Amazon items)'

        # Normalize entries from the feed
        entries = normalize_entries(feed.entries)

        # Run through all the normalized entries...
        for e in entries:
            
            # Perform a search on the entry title, extract the items
            result = self.amazon_search(e['summary'])
            items  = [ x for x in result.Items if 'Item' in x._name ]
            
            # Use each search result item to populate the templates.
            insert_items = [ self.INSERT_ITEM_TMPL % {
                'title' : i.ItemAttributes.Title,
                'url'   : i.DetailPageURL,
                'img'   : i.SmallImage.URL
            } for i in items[:self.MAX_ITEMS] ]
            insert_out = self.INSERT_TMPL % '\n'.join(insert_items)

            # Append the rendered search results onto the entry summary.
            e.data['summary'] += insert_out.decode('utf-8', 'ignore')
            
        return entries

    def amazon_search(self, query):
        """
        Given a query string, perform an Amazon search.
        """
        # Construct an Amazon search URL and fetch it.
        args = {
            'SubscriptionId' : self.AMAZON_KEY,
            'AssociateTag'   : self.ASSOCIATE_TAG,
            'Service'        : 'AWSECommerceService',
            'Operation'      : 'ItemSearch',
            'ResponseGroup'  : 'Medium,ItemAttributes',
            'SearchIndex'    : 'Books',
            'TextStream'     : query
        }
        url  = "http://webservices.amazon.com/onca/xml?%s" % \
            urllib.urlencode(args)
        
        # Parse and return the results of the search
        data = HTTPCache(url).content()
        doc  = xmltramp.parse(data)
        return doc

if __name__=='__main__': main()

