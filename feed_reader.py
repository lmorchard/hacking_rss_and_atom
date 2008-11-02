#!/usr/bin/env python

import sys
#import minifeedparser as feedparser
import feedparser

if __name__ == '__main__':
    feed_uri  = sys.argv[1]
    feed_data = feedparser.parse(feed_uri)
    
    print "============================================================" 
    print "'%(title)r' at %(link)r" % feed_data['feed']
    print "============================================================" 
    print 

    for entry in feed_data['entries']:
        print "------------------------------------------------------------" 
        print "Date:  %(modified)r" % entry
        print "Title: %(title)r" % entry
        print "Link:  %(link)r" % entry
        
        if not entry.get('summary', '') == '':
            print
            print "%(summary)r" % entry

        print "------------------------------------------------------------" 
        print

