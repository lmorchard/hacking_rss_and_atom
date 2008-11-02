#!/usr/bin/env python
"""
ch16_feed_delicious_recaps.py

Insert del.icio.us link recaps into a normalized feed.
"""
import sys, time, urllib2, feedparser, xmltramp
from httpcache import HTTPCache
from xml.sax import SAXParseException
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries

FEED_URL = 'http://www.decafbad.com/blog/atom.xml' 

def main():
    """
    Use the DeliciousFeed on a given feed.
    """
    feed_url = ( len(sys.argv) > 2 ) and sys.argv[2] or FEED_URL

    f = DeliciousFeed(feed_url)
    f.STATE_FN = 'link_delicious_recaps_state'
    f.DEL_USER, f.DEL_PASSWD = \
        open('delicious-acct.txt').read().strip().split(':')
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print f.scrape_rss()
    else:
        print f.scrape_atom()
    
class DeliciousFeed(Scraper):
    """
    Insert daily recaps of del.icio.us links as entries
    into a normalized feed.
    """
    DEL_API_URL = "http://del.icio.us/api/posts/get?dt=%s"
    DEL_USER, DEL_PASSWD = "user", "passwd"
    NUM_DAYS = 6
    
    DEL_ENTRY_TMPL = """
        <ul>
        %s
        </ul>
    """
    DEL_LINK_TMPL = """
        <li>
            <a href="%(href)s">%(description)s</a> (%(tags)s)<br />
            %(extended)s
        </li>
    """
    DEL_TAG_TMPL = """<a href="%(href)s">%(tag)s</a> """
    
    def __init__(self, main_feed):
        """Initialize with the feed URI for parsing."""
        self.main_feed = main_feed

    def produce_entries(self):
        """
        Normalize the source feed, insert del.icio.us daily link recaps.
        """
        # Grab and parse the feed
        feed = feedparser.parse(HTTPCache(self.main_feed).content())
        
        # Normalize feed meta data
        self.FEED_META = normalize_feed_meta(feed, self.date_fmt)
        self.FEED_META['feed.title'] += ' (with del.icio.us links)'

        # Normalize entries from the feed
        entries = normalize_entries(feed.entries)

        # Iterate through a number of past days' links
        for n in range(self.NUM_DAYS):

            # Calculate and format date for this query
            post_secs = time.time() - ( (n+1) * 24 * 60 * 60 ) 
            post_time = time.localtime(post_secs)
            post_dt   = time.strftime('%Y-%m-%d', post_time)

            # Prepare for Basic Authentication in calling del API
            auth = urllib2.HTTPBasicAuthHandler()    
            auth.add_password('del.icio.us API', 'del.icio.us', 
                              self.DEL_USER, self.DEL_PASSWD)
            urllib2.install_opener(urllib2.build_opener(auth))
            
            # Build del API URL, execute the query, and parse response.
            url  = self.DEL_API_URL % post_dt
            data = HTTPCache(url).content()
            doc  = xmltramp.parse(data)

            # Skip this day if no posts resulted from the query
            if not len(doc) > 0: continue

            # Iterate through all posts retrieved, build content for entry.
            post_out = []
            for post in doc:
                
                # Run through post tags, render links with template.
                tags_out = [ self.DEL_TAG_TMPL % {
                    'tag'  : t,
                    'href' : 'http://del.icio.us/%s/%s' % (self.DEL_USER, t)
                } for t in post("tag").split() ]
                
                # Build content for this link posting using template.
                try:    extended = post('extended')
                except: extended = ''

                post_out.append(self.DEL_LINK_TMPL % {
                    'href'        : post('href'),
                    'description' : post('description'),
                    'extended'    : extended,
                    'tags'        : ''.join(tags_out)
                })
                    
            # Construct and append a new feed entry based on the day's links
            new_entry = FeedEntryDict(date_fmt=self.date_fmt, init_dict={
                'title'    : 'del.icio.us links on %s' % post_dt,
                'issued'   : post_secs,
                'modified' : post_secs,
                'link'     : 'http://del.icio.us/%s#%s' % \
                             (self.DEL_USER, post_dt),
                'summary'  : self.DEL_ENTRY_TMPL % "\n".join(post_out)
            })
            entries.append(new_entry)
        
            # Pause, because http://del.icio.us/doc/api says so.
            time.sleep(1) 
            
        # Return the list of entries built
        return entries

if __name__=='__main__': main()
