#!/usr/bin/env python
"""
Syndic8Client.py

This module implements a feed search using web services available 
at Syndic8.com
"""

import sys, xmlrpclib

FEED_TYPES = { 'RSS'  : 'application/rss+xml',
               'Atom' : 'application/atom+xml' }

def getFeedsDetail(url):
    feeds    = []
    server   = xmlrpclib.Server('http://www.syndic8.com/xmlrpc.php')
    feedids  = server.syndic8.QueryFeeds('siteurl', 'like', 
                   url+'%', 'headlines_rank')
    infolist = server.syndic8.GetFeedInfo(feedids, 
                   ['status','sitename','format','dataurl'])

    for f in infolist:
        if f['status'] != 'Dead':
            feeds.append({
                'type'  : FEED_TYPES.get(f['format'], "unknown"),
                'title' : f['sitename'],
                'href'  : f['dataurl']
            })

    return feeds

def getFeeds(self, url):
    return [ x['href'] for x in getFeedsDetail(url) ]
    
def main():
    url    = sys.argv[1]
    feeds  = getFeedsDetail(url)
    
    print
    print "Found the following possible feeds at %s:" % url
    for feed in feeds:
        print "\t '%(title)s' of type %(type)s at %(href)s" % feed
    print

if __name__ == "__main__": main()
