#!/usr/bin/env python
"""
ch08_feedfilter.cgi

Filter a feed through cgi_buffer.
"""
import cgi_buffer

FEED_FN   = "sample_rss.xml"
FEED_TYPE = "rss"

def main():
    print "Content-Type: application/%s+xml" % FEED_TYPE
    print
    print open(FEED_FN, 'r').read()

if __name__=='__main__': main()
