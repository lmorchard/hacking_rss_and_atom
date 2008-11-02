#!/usr/bin/env python
"""
ch14_feed_normalizer.py

Use feedparser and scraperlib to normalize feed content.
"""
import sys, calendar, time
import feedparser
from scraperlib import FeedEntryDict, Scraper

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    feed_uri = sys.argv[2]
    scraper  = FeedNormalizer(feed_uri)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()
    
class FeedNormalizer(Scraper):
    """
    Uses feedparser data to rebuild normalized feeds.
    """
    STATE_FN     = 'normalizer_state'
    FULL_CONTENT = True

    def __init__(self, feed_uri=None):
        """Initialize with the feed URI for parsing."""
        self.feed_uri = feed_uri

    def produce_entries(self):
        """Use normalize_feed() to generate normalized entries"""
        feed = feedparser.parse(self.feed_uri)
        
        self.FEED_META = normalize_feed_meta(feed, self.date_fmt)
        
        entries = normalize_entries(feed.entries, self.FULL_CONTENT)
        for e in entries:
            e.date_fmt = self.date_fmt

        return entries

def normalize_feed_meta(feed_parsed, date_fmt):
    """
    Produce normalized feed metadata from a parsed feed.
    """
    feed_in = feed_parsed.feed

    # Build the initial feed metadata map
    feed_meta = {
        'feed.title'        : feed_in.get('title', 'untitled'),
        'feed.link'         : feed_in.get('link', ''),
        'feed.tagline'      : feed_in.get('tagline', ''),
        'feed.author.name'  : 'unnamed',
        'feed.author.email' : 'example@example.com',
        'feed.author.url'   : 'http://www.example.com',
    }

    # Update the output feed's modified time if incoming feed has it
    if feed_in.has_key('modified_parsed'):
        feed_meta['feed.modified'] = \
            time.strftime(date_fmt, feed_in.modified_parsed)
    else:
        feed_meta['feed.modified'] = \
            time.strftime(date_fmt, time.gmtime())
    
    # Copy incoming feed author details, if any.
    if feed_in.has_key('author_detail'):
        feed_meta['feed.author.name']  = \
            feed_in.author_detail.get('name','')
        feed_meta['feed.author.email'] = \
            feed_in.author_detail.get('email','')
        feed_meta['feed.author.url']   = \
            feed_in.author_detail.get('url','')
            
    # Copy incoming feed author name, if not details.
    elif feed_in.has_key('author'):
        feed_meta['feed.author.name'] = feed_in.author

    return feed_meta
    
def normalize_entries(entries_in, full_content=True):
    """
    Return a list of normalized FeedEntryDict objects, given a
    list of entries from the feedparser.
    """
    entries = []
    
    # Process incoming feed entries.
    for entry_in in entries_in:
        
        # Create the empty new output feed entry.
        entry_out = FeedEntryDict()

        entry_out.orig = entry_in

        # Perform a straight copy of a few entry attributes.
        for n in ('id', 'title', 'link'):
            if entry_in.has_key(n):
                entry_out[n] = entry_in[n]

        # Convert feedparser time tuples to seconds and copy over.
        for n in ('modified', 'issued'):
            if entry_in.get('%s_parsed' % n, None):
                entry_out[n] = calendar.timegm(entry_in['%s_parsed' % n])
        
        # Decide whether to copy only summary or full content.
        if full_content and entry_in.has_key('content'):
            content_list = [ x.value for x in entry_in.content 
                             if 'text' in x.type ]
            entry_out['summary'] = ''.join(content_list)
        elif entry_in.has_key('summary'):
            entry_out['summary'] = entry_in.summary
            
        # Append finished feed to list.
        entries.append(entry_out)

    # Return accumulated output feed entries.
    return entries

if __name__=='__main__': main()
