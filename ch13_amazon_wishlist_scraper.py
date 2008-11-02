"""
ch13_amazon_wishlist_scraper.py

Use the Amazon API to look up items for a wishlist.
"""
import sys, urllib, xmltramp
from amazonlib import AmazonScraper
from httpcache import HTTPCache

AWS_ID          = open("amazon-key.txt", "r").read().strip()
AWS_WISHLIST_ID = "1QWYI6P2JF3Q5"

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = AmazonWishlistScraper(AWS_ID, AWS_WISHLIST_ID)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class AmazonWishlistScraper(AmazonScraper):
    """
    Produce a feed from Amazon wishlist items
    """
    FEED_META = {
        'feed.title'        : 'Amazon WishList items',
        'feed.link'         : 'http://www.amazon.com',
        'feed.tagline'      : 'Search results from Amazon.com',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }

    STATE_FN = 'amazon_wishlist_state'

    def __init__(self, id, wishlist_id):
        """Initialize with AWS id and wishlist id"""
        self.aws_id      = id
        self.wishlist_id = wishlist_id

    def fetch_items(self):
        """
        Grab search result items for given index and keywords.
        """
        # Construct the list of arguments for the AWS query
        args = {
            'Service'        : 'AWSECommerceService',
            'Operation'      : 'ListLookup',
            'ResponseGroup'  : 'Medium,ListFull,ItemAttributes',
            'Sort'           : 'LastUpdated',
            'ListType'       : 'WishList',
            'ListId'         : self.wishlist_id,
            'SubscriptionId' : self.aws_id,
        }
        
        # Build the URL for the API call using the base URL and params.
        url = "%s?%s" % (self.AWS_URL, urllib.urlencode(args))
        
        # Perform the query, fetch and parse the results.
        data  = HTTPCache(url).content()
        doc   = xmltramp.parse(data)
        
        # Update the feed link and title from search result metadata
        self.FEED_META['feed.link']  = doc.Lists.List.ListURL
        self.FEED_META['feed.title'] = \
            'Amazon.com wishlist items for "%s"' % \
            doc.Lists.List.CustomerName
        
        # Fetch first page of items.
        return [ x.Item for x in doc.Lists.List if 'ListItem' in x._name ]
    
if __name__ == "__main__": main()
