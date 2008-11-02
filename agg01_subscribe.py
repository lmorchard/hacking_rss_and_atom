#!/usr/bin/env
"""
agg01_subscribe.py

Given a URI, try to find feeds there and subscribe to one.
"""
import sys, feedfinder

FEEDS_FN = "feeds.txt"

uri = sys.argv[1]

try:
    feeds = feedfinder.getFeeds(uri)
except:
    feeds = []

if len(feeds) == 0:
    print "No feeds found at %s" % uri 

elif len(feeds) > 1:
    print "Multiple feeds found at %s" % uri
    for feed_uri in feeds:
        print "\t%s" % feed_uri

else:
    feed_uri = feeds[0]
    try:
        subs = [x.strip() for x in open(FEEDS_FN).readlines()]
    except:
        subs = []
    
    if feed_uri in subs:
        print "Already subscribed to %s" % feed_uri
    else:
        subs.append(feed_uri)
        open(FEEDS_FN, "w").write("\n".join(subs))
        print "Subscribed to %s" % feed_uri

