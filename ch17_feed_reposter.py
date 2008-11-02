#!/usr/bin/env python
"""
ch17_feed_reposter.py

Republish feed entries to a metaWeblogAPI server.
"""
import sys, time, xmlrpclib
from agglib import openDBs, closeDBs, getNewFeedEntries

FEEDS_FN    = "reposter_uris.txt"
FEED_DB_FN  = "reposter_feeds_db"
ENTRY_DB_FN = "reposter_entry_seen_db"

API_URI     = "http://www.example.com/mt/mt-xmlrpc.cgi"
API_USER    = "your_username_here"
API_PASSWD  = "your_passwd_here"
API_BLOGID  = 1

def main():
    """
    Process new feed entries and repost to the blog API.
    """
    # Get a handle on the blog API server
    srv = xmlrpclib.ServerProxy(API_URI, verbose=0)

    # Open up the databases, load the subscriptions, get new entries.
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)
    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    for e in getNewFeedEntries(feeds, feed_db, entry_db):
        
        # Get the entry and feed metadata.
        feed, entry = e.data.feed, e.entry
        
        # Build a blog post title using feed and entry titles.
        title = u'%s &#8212; %s' % ( feed.get('title', u'untitled'),
                                     entry.get('title', u'untitled') )      
        
        # Generate an ISO8601 date using the feed entry modification,
        # with current date/time as default.
        date = time.strftime('%Y-%m-%dT%H:%M:%SZ', 
                             entry.get('modified_parsed', 
                                       time.gmtime()))
        
        # Build blog post body content from what's available in the
        # feed entry.
        content_out = []
        if entry.has_key('summary'):
            content_out.append(entry.summary)
        content_out.extend([ c.value for c in entry.get('content', [])
                             if 'html' in c.type ])
        content = '<br />\n'.join(content_out) 
            
        # Build the blog post content from feed and entry.
        desc = u"""
            %(content)s
            <br />
            [ <a href="%(entry.link)s">Originally</a> posted 
              at <a href="%(feed.link)s">%(feed.title)s</a> ]
        """ % {
            'content'       : content,
            'entry.link'    : entry.get('link', u''),
            'feed.title'    : feed.get('title', u''),
            'feed.link'     : feed.get('link', u''),
        }
        
        # Build post item data, call blog API via XML-RPC
        post  = {
            'title'             : title,
            'dateCreated'       : date,
            'description'       : desc,
            'mt_convert_breaks' : False
        }
        try:
            srv.metaWeblog.newPost(API_BLOGID, API_USER, API_PASSWD,
                                   post, True)
            print "Posted %s" % title
        except KeyboardInterrupt:
            raise
        except:
            print "Problem posting %s" % title
    
if __name__=='__main__': main()
