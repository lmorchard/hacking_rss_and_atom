#!/usr/bin/env python
"""
ch13_amazon_find_wishlist.py

Given search terms as a command line argument, look for wishlists.
"""
import sys, urllib, xmltramp
from httpcache import HTTPCache

AWS_ID  = open("amazon-key.txt", "r").read().strip()
AWS_URL = "http://webservices.amazon.com/onca/xml"

def main():
    """
    Search for wishlists using command line arguments.
    """
    # Leaving out the program name, grab all space-separated arguments.
    name   = " ".join(sys.argv[1:])
    
    # Construct the list of arguments for the AWS query
    args = {
        'Service'        : 'AWSECommerceService',
        'Operation'      : 'ListSearch',
        'ListType'       : 'WishList',
        'SubscriptionId' : AWS_ID,
        'Name'           : name
    }
    
    # Build the URL for the API call using the base URL and params.
    url = "%s?%s" % (AWS_URL, urllib.urlencode(args))
    
    # Perform the query, fetch and parse the results.
    data  = HTTPCache(url).content()
    doc   = xmltramp.parse(data)
    
    # Print out the list IDs found.
    lists = [ x for x in doc.Lists if 'List' in x._name ]
    for list in lists:
        print '%15s: %s' % ( list.ListId, list.CustomerName )

if __name__=="__main__": main()
