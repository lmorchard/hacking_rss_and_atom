#!/usr/bin/env python
"""
ch13_amazon_search_scraper.py

Produce a feed from a given Amazon product search.
"""
import sys, urllib, xmltramp
from amazonlib import AmazonScraper
from httpcache import HTTPCache

AWS_ID       = open("amazon-key.txt", "r").read().strip()
AWS_INDEX    = "Books"
AWS_KEYWORDS = "ExtremeTech"

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = AmazonSearchScraper(AWS_ID, AWS_INDEX, AWS_KEYWORDS)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class AmazonSearchScraper(AmazonScraper):
    """
    Produce feeds from Amazon product searches.
    """
    FEED_META = {
        'feed.title'        : 'Search Feed',
        'feed.link'         : 'http://www.amazon.com',
        'feed.tagline'      : 'Search results from Amazon.com',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }

    STATE_FN = 'amazon_search_state'

    def __init__(self, id, index, keywords):
        """
        Initialize with AWS id and wishlist id.
        """
        self.aws_id   = id
        self.index    = index
        self.keywords = keywords
        
        self.FEED_META['feed.title'] = \
            'Amazon.com search for "%s" in %s' % \
            (self.keywords, self.index)

    def fetch_items(self):
        """
        Grab search result items for given index and keywords.
        """
        # Construct the list of arguments for the AWS query
        args = {
            'Service'        : 'AWSECommerceService',
            'Operation'      : 'ItemSearch',
            'ResponseGroup'  : 'Medium',
            'SearchIndex'    : self.index,
            'Keywords'       : self.keywords,
            'SubscriptionId' : self.aws_id,
        }
        
        # Build the URL for the API call using the base URL and params.
        url = "%s?%s" % (self.AWS_URL, urllib.urlencode(args))
        
        # Perform the query, fetch and parse the results.
        data  = HTTPCache(url).content()
        doc   = xmltramp.parse(data)
        
        # Fetch first page of items.
        items = [ x for x in doc.Items if 'Item' in x._name ] 
        return items 
        
if __name__ == "__main__": main()
