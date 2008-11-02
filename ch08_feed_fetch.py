#!/usr/bin/env python
"""
ch08_feed_fetch.py

Fetch a feed and print to standard output.
"""
import sys
from httpcache import HTTPCache

def main():
    """
    Given a feed URL as an argument, fetch and print the feed.
    """
    feed_uri     = sys.argv[1]
    cache        = HTTPCache(feed_uri)
    feed_content = cache.content()

    print feed_content

if __name__ == "__main__": main()

