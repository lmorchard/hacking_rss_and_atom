#!/usr/bin/env python
"""
ch13_amazon_find_wishlist_2.py

Given search terms as a command line argument, look for wishlists.
"""
import sys
from amazonlib import AmazonAPI

AWS_ID = "15JJ72YYQY34NCAK46R2"

def main():
    """
    Search for wishlists using command line arguments.
    """
    # Leaving out the program name, grab all space-separated arguments.
    name = " ".join(sys.argv[1:])
    
    # Create and instance of the Amazon API wrapper
    api = AmazonAPI(AWS_ID)
    
    # Perform a ListSearch query for the wishlist
    meta, results = api.ListSearch("WishList", name)

    # Print out the list IDs found.
    print '\n'.join([ x['ListId'] for x in results ])
    
if __name__=="__main__": main()
