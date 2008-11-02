#!/usr/bin/env python
"""
ch17_feed_blog.py

Republish feed entries as a static HTML blog.
"""
import sys, os, time, calendar, pickle
from agglib import openDBs, closeDBs
from agglib import getNewFeedEntries, writeAggregatorPage

FEEDS_FN    = "feed_blog_uris.txt"
FEED_DB_FN  = "feed_blog_feeds_db"
ENTRY_DB_FN = "feed_blog_entry_seen_db"
HISTORY_FN  = "feed_blog_history_db"
BLOG_FN     = "feed_blog.html"
ARCHIVE_FN  = "feed_blog_%Y%m%d_%H%M%S.html"
MAX_ENTRIES = 25

def main():
    """
    Fire up the feed blog generator, write the static HTML to disk.
    """
    # Try to load up entry history, start with an empty list in
    # case of any problems.
    try:    entries = pickle.load(open(HISTORY_FN, 'rb'))
    except: entries = []
    
    # Open up the databases, load the subscriptions, get new entries.
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)
    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]

    # Gather new entries from all feeds.
    subs_details = []
    for feed_uri in feeds:

        # HACK: Grab 'custom' feed record details before agglib update.
        if feed_db.has_key(feed_uri):
            feed_rec   = feed_db[feed_uri]
            feed_link  = feed_rec.get('link',  '#')
            feed_title = feed_rec.get('title', 'untitled')
            
        # Get new entries, if any.
        new_entries = getNewFeedEntries([feed_uri], feed_db, entry_db)

        # If there's no record of the feed in the DB, skip it.
        if not feed_db.has_key(feed_uri): continue
        
        # Update feed record details from fresh feed, if any entries found.
        if len(new_entries) > 0:
            feed       = new_entries[0].data.feed
            feed_link  = feed.get('link',  '#')
            feed_title = feed.get('title', 'untitled')
        
        # HACK: Update 'custom' feed record details after agglib update.
        feed_rec = feed_db[feed_uri]
        feed_rec['link']  = feed_link
        feed_rec['title'] = feed_title
        feed_db[feed_uri] = feed_rec
        
        # Add details for this feed to the sidebar content.
        subs_details.append({
            'feed.link'  : feed_link,
            'feed.title' : feed_title,
            'feed.url'   : feed_uri
        })
        
        # Skip ahead if no new entries found.
        if len(new_entries) < 1: continue
            
        # Make sure entries have a modified date, using now by default.
        for e in new_entries:
            if not e.entry.has_key('modified_parsed'):
                e.entry['modified_parsed'] = time.gmtime()

        # Tack the list of new entries onto the head of the main list.
        entries = new_entries + entries
    
    # Sort the subscription details, build the sidebar content.
    subs_details.sort(lambda a,b: cmp( a['feed.title'], 
                                       b['feed.title'] ))
    subs_out = [ SUBSCRIPTION_TMPL % x for x in subs_details ]
    
    # Sort all the entries, truncate to desired length.
    entries.sort()
    entries = entries[:MAX_ENTRIES]

    # Write out the current run's aggregator report.
    out_fn = time.strftime(ARCHIVE_FN)
    writeAggregatorPage(entries, out_fn, DATE_HDR_TMPL, FEED_HDR_TMPL, 
        ENTRY_TMPL, PAGE_TMPL)
    
    # Build the page template from the template template.
    out = SHELL_TMPL % {
        'subs' : '\n'.join(subs_out),
        'main' : open(out_fn).read()
    }
    open(BLOG_FN, 'w').write(out)
    
    # Close the databases and save the entry history back out to disk.
    closeDBs(feed_db, entry_db)
    pickle.dump(entries, open(HISTORY_FN, 'wb'))

# Presentation templates for output follow:
    
SUBSCRIPTION_TMPL = u"""
    <li>
        [<a href="%(feed.url)s">feed</a>]
        <a href="%(feed.link)s">%(feed.title)s</a>
    </li>
"""

PAGE_TMPL = "%s"

DATE_HDR_TMPL = """
    <h1 class="dateheader">%s</h1>
"""

FEED_HDR_TMPL = """
    <h2 class="feedheader"><a href="%(feed.link)s">%(feed.title)s</a></h2>
"""

ENTRY_TMPL = u"""
    <div class="feedentry">
        <div class="entryheader">
            <span class="entrytime">%(time)s</span>: 
            <a class="entrylink" href="%(entry.link)s">%(entry.title)s</a>
        </div>
        <div class="entrysummary">
            %(entry.summary)s
        </div>
    </div>
"""

SHELL_TMPL = u"""
<html>
    <head>
        <style>
            body {
                font-family: sans-serif;
                font-size: 12px;
            }
            .subscriptions {
                float: right;
                clear: right;
                width: 220px;
                padding: 10px;
                border: 1px solid #444;
            }
            .main {
                margin-right: 240px;
            }
            .pageheader {
                font-size: 2em;
                font-weight: bold;
                border-bottom: 3px solid #000;
                padding: 5px;
            }
            .dateheader   { 
                 margin: 20px 10px 10px 10px; 
                 border-top: 2px solid #000; 
                 border-bottom: 2px solid #000; 
            }
            .feedheader   { 
                 margin: 20px;
                 border-bottom: 1px dashed #aaa;
            }
            .feedentry    { 
                margin: 10px 30px 10px 30px; 
                padding: 10px; 
                border: 1px solid #ddd;
            }
            .entryheader {
                border-bottom: 1px solid #ddd;
                padding: 5px;
            }
            .entrytime {
                font-weight: bold;
            }
            .entrysummary { 
                margin: 10px; 
                padding: 5px; 
            }
        </style>
    </head>
    <body>
        <h1 class="pageheader">Feed blog central</h1>
        <div class="subscriptions">
            <b>Subscriptions:</b>
            <ul>
                %(subs)s
            </ul>
        </div>
        <div class="main">
            %(main)s
        </div>
    </body>
</html>
"""

if __name__=="__main__": main()
