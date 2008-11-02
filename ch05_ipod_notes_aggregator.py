#!/usr/bin/env python
"""
ch05_ipod_notes_aggregator.py

Poll subscriptions, load iPod up with notes.
"""
import sys, os, os.path, shutil, time, md5
from agglib import *

FEEDS_FN        = "ipod_feeds.txt"
FEED_DB_FN      = "ipod_feeds_db"
ENTRY_DB_FN     = "ipod_entry_seen_db"

IPOD_NOTES_PATH      = "/Volumes/Spirit of Radio/Notes"
IPOD_FEEDS_IDX_TITLE = "Feeds"
IPOD_FEEDS_IDX       = "feeds.linx"
IPOD_FEEDS_DIR       = "zz_feeds"

NOTE_TMPL = """
<html>
    <head>
        <title>%(title)s</title>
        <meta name="ShowBodyOnly" content="true">
        <meta name="HideAllTags" content="true">
        <meta name="LineWrap" content="true">
        <meta name="NowPlaying" content="false">
    </head>
    <body>%(content)s</body>
</html>
"""

FEED_LINK_TMPL  = """<a href="%(href)s">%(title)s</a><br>\n"""

ENTRY_LINK_TMPL = """* <a href="%(href)s">%(title)s</a><br>\n"""

ENTRY_TMPL      = """<b>%(entry.title)s</b><br>
%(date)s - %(time)s<br>
<br>
%(entry.summary)s
"""

def main(): 
    """
    Poll subscribed feeds and load the iPod up with notes.
    """
    # Open the aggregator databases
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)
    
    # Clean up and recreate feed notes directory
    ipod_feeds_path = os.path.join(IPOD_NOTES_PATH, IPOD_FEEDS_DIR)
    shutil.rmtree(ipod_feeds_path, ignore_errors=True)
    os.makedirs(ipod_feeds_path)

    # Load up the list of subscriptions
    feeds = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    # Build the notes for all feeds, gathering links to the feed indexes
    feed_links = buildNotesForFeeds(feed_db, entry_db, ipod_feeds_path, feeds)
    
    # Write the feed index note with links to all feed indexes
    index_out = "".join([FEED_LINK_TMPL % f for f in feed_links])
    writeNote(filename = os.path.join(IPOD_NOTES_PATH, IPOD_FEEDS_IDX),
              title    = IPOD_FEEDS_IDX_TITLE, 
              content  = index_out)
    
    # Close the aggregator databases
    closeDBs(feed_db, entry_db)

def buildNotesForFeeds(feed_db, entry_db, ipod_feeds_path, feeds):
    """
    Iterate through feeds, produce entry notes, feed index notes,
    and return list of links to feed index notes.
    """
    feed_links = []
    for feed_url in feeds:
        
        # Get new entries for the current feed
        entries = getNewFeedEntries([feed_url], feed_db, entry_db)
        if len(entries) > 0:
            
            # Derive current feed path via md5 hash, create it if needed
            feed_dir_name = md5_hash(feed_url)
            feed_dir      = os.path.join(ipod_feeds_path, feed_dir_name)
            if not os.path.isdir(feed_dir): 
                os.makedirs(feed_dir)
        
            # Get a clean title for this feed.
            feed_title = feed_db[feed_url].get('title', 'Untitled').strip()
            
            # Build the notes for the new entries, gathering links
            feed_entry_links = buildNotesForEntries(feed_dir, feed_title, entries)

            # Write out the index note for this feed, based on entry notes.
            feed_out = "".join([ENTRY_LINK_TMPL % f for f in feed_entry_links])
            writeNote(filename = os.path.join(feed_dir, 'index.txt'),
                      title    = feed_title, 
                      content  = feed_out)
            
            # Include this feed in the top-level index.
            feed_links.append({
                'href'  : '%s/%s/index.txt' % (IPOD_FEEDS_DIR, feed_dir_name),
                'title' : feed_title
            })

    return feed_links

def buildNotesForEntries(feed_dir, feed_title, entries):
    """
    Iterate through a set of entries, build a note for each in the
    appropriate feed directory, return list of links to generated
    notes.
    """
    feed_entry_links = []
    for entry in entries:
        
        # Build note name on MD5 hash, possibly redundant but oh well!
        entry_note_name = '%s.txt' % md5_hash(entry.hash())
        
        # Get a clean title for the entry note
        entry_title     = entry['entry.title'].strip()
        
        # Write out the index note for this feed.
        writeNote(filename = os.path.join(feed_dir, entry_note_name),
                  title    = feed_title, 
                  content  = ENTRY_TMPL % entry)
        
        # Include this feed in the top-level index
        feed_entry_links.append({
            'href'  : entry_note_name,
            'title' : entry_title
        })

    return feed_entry_links

def writeNote(filename, title, content):
    """
    Given a filename, title, and content, write a note to the iPod.
    """
    print "\t\tWrote note: %s" % filename
    fout = open(filename, "w")
    fout.write(NOTE_TMPL % { 'title':title, 'content':content })
    fout.close()

def md5_hash(data):
    """
    Convenience function to generate an MD5 hash.
    """
    m = md5.md5()
    m.update(data)
    return m.hexdigest()

if __name__ == "__main__": main()
