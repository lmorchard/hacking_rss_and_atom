#!/usr/bin/env python
"""
ch06_enclosure_finder.py

Given the URL to a feed, list the URLs of enclosures found.
"""

import sys, feedparser

def main():
    feed_url = sys.argv[1]
    feed     = feedparser.parse(feed_url)
    enc_urls = getEnclosuresFromEntries(feed.entries)
    print "\n".join(enc_urls)

def getEnclosuresFromEntries(entries):
    """
    Given a set of entries, harvest the URLs to enclosures.
    """
    enc_urls = []
    for entry in entries:
        enclosures = entry.get('enclosures',[])
        enc_urls.extend([ en['url'] for en in enclosures ])
    return enc_urls

if __name__ == "__main__": main()
