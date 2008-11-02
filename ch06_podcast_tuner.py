#!/usr/bin/env python
"""
ch06_podcast_tuner.py

Poll subscriptions and download new enclosures.
"""
import sys, time, os.path
from agglib      import *
from downloaders import *
from mp3players  import *

FEEDS_FN        = "podcast_feeds.txt"
FEED_DB_FN      = "podcast_feeds_db"
ENTRY_DB_FN     = "podcast_entry_seen_db"
DOWNLOAD_PATH   = "enclosures/%s" % time.strftime("%Y-%m-%d") 
NEW_FEED_LIMIT  = 1
MP3PLAYER       = iTunesMac()
VALID_AUDIO_EXT = ( ".mp3", ".mp4", ".m4p", ".wav", ".aiff" )

def main(): 
    """
    Poll subscribed feeds, find enclosures, download content, and
    try importing audio files into the MP3 player.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    # Create current download path, if need be
    if not os.path.isdir(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
        
    # Read in the list of subscriptions
    feeds = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    for feed in feeds:
        # Has this feed been seen before?
        new_feed = not feed_db.has_key(feed)

        # Get new entries for feed, skip to next feed if none.
        entries = getNewFeedEntries([feed], feed_db, entry_db)
        if not len(entries) > 0: continue
            
        # Collect all the enclosure URLs found in new entries.
        enc_urls = getEnclosuresFromEntries(entries)
        if not len(enc_urls) > 0: continue
            
        # If this is a new feed, only grab a limited number of 
        # enclosures.  Otherwise, grab all of them.
        down_limit = new_feed and NEW_FEED_LIMIT or len(enc_urls)
        
        # Download the enclosures.
        print "\tDownloading enclosures..."
        files = downloadURLs(DOWNLOAD_PATH, enc_urls[:down_limit])
                
        # Import downloaded files into audio player
        if files:
            print "\tImporting the enclosures..."
            importAudioFiles(MP3PLAYER, VALID_AUDIO_EXT, files)
        
    closeDBs(feed_db, entry_db)

def getEnclosuresFromEntries(entries):
    """
    Given a set of entries, harvest the URLs to enclosures.
    """
    enc_urls = []
    for e in entries:
        enclosures = e.entry.get('enclosures',[])
        enc_urls.extend([ en['url'] for en in enclosures ])
    return enc_urls

def downloadURLs(download_path, urls):
    """
    Given a set of URLs, attempt to download their content.
    """
    for url in urls:
        try:
            if url.endswith(".torrent"):
                dl = BitTorrentDownloader()
            else:
                dl = HTTPDownloader()
            return dl.downloadURL(download_path, url)
        except KeyboardInterrupt:
            raise
        except Exception, e:
            print "\n\t\tProblem downloading %s: %s" % (url, e)

def importAudioFiles(player, valid_exts, files):
    """
    Given an MP3 player and list of files, attempt to import any 
    valid audio files.
    """
    files = [f for f in files if isValidAudioFile(valid_exts, f) ]
    for file in files:
        try:
            print "\t\t%s" % file
            player.addTrack(file)
        except KeyboardInterrupt:
            raise
        except Exception, e:
            print "\n\t\tProblem importing %s: %s" % (file, e)
            
def isValidAudioFile(valid_exts, file):
    """
    Given the path to a file, determine whether it is a 
    valid audio file.
    """
    if not os.path.exists(file): return False
    for ext in valid_exts:
        if file.endswith(ext): return True
    return False
        
if __name__=="__main__": main()
