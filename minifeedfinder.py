#!/usr/bin/env python
"""
FeedAutodiscoveryParser.py

This module implements a simple feed autodiscovery technique using 
HTMLParser from the standard Python library.
"""

import sys
from urllib2    import urlopen
from urlparse   import urljoin
from HTMLParser import HTMLParser, HTMLParseError

class FeedAutodiscoveryParser(HTMLParser):
    """
    This class extracts feed candidate links from HTML.
    """
    
    # These are the MIME types of links accepted as feeds
    FEED_TYPES = ('application/rss+xml',
                  'text/xml',
                  'application/atom+xml',
                  'application/x.atom+xml',
                  'application/x-atom+xml')
    
    def __init__(self, base_href):
        """
        Initialize the parser
        """
        HTMLParser.__init__(self)
        self.base_href = base_href
        self.feeds     = []
        
    def handle_starttag(self, tag, attrs_tup):
        """
        While parsing HTML, watch out for <base /> and <link /> tags. 
        Accumulate any feed-candidate links found.
        """
        # Turn the tag name to lowercase for easier comparison, and
        # make a dict with lowercase keys for the tag attributes
        tag   = tag.lower()
        attrs = dict([(k.lower(), v) for k,v in attrs_tup])
        
        # If we find a <base> tag with new HREF, change the current base HREF
        if tag == "base" and 'href' in attrs:
            self.base_href = attrs['href']
            
        # If we find a <link> tag, check it for feed candidacy.
        if tag == "link":
            
            # Extract the standard link attributes
            rel   = attrs.get("rel", "")
            type  = attrs.get("type", "")
            title = attrs.get("title", "")
            href  = attrs.get("href", "")

            # Check if this link is a feed candidate, add to the list if so.
            if rel == "alternate" and type in self.FEED_TYPES:
                self.feeds.append({
                    'type'  : type,
                    'title' : title,
                    'href'  : href
                })

def getFeedsDetail(url):
    """
    Load up the given URL, parse, and return any feeds found.
    """
    data   = urlopen(url).read()
    parser = FeedAutodiscoveryParser(url)
    
    try:
        parser.feed(data)
    except HTMLParseError:
        # Ignore any parse errors, since HTML is dirty and what we want
        # should be early on in the document anyway.
        pass
    
    # Fix up feed HREFs, converting to absolute URLs using the base HREF.
    for feed in parser.feeds:
        feed['href'] = urljoin(parser.base_href, feed['href'])
        
    return parser.feeds

def getFeeds(url):
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
