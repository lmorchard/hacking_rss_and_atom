#!/usr/bin/env python
"""
ch05_speech_aggregator.py

Poll subscriptions, produce plain text script, recite into a sound file,
then attempt to import into iTunes and an iPod.
"""
import sys, os, os.path, time
from agglib import *
from HTMLParser import HTMLParser

TXT_FN        = "speech-aggregator-%s.txt" % time.strftime("%Y%m%d-%H%M%S")
SOUND_FN      = "speech-aggregator-%s.aiff" % time.strftime("%Y%m%d-%H%M%S")
FEEDS_FN      = "speech_feeds.txt"
FEED_DB_FN    = "speech_feeds_db"
ENTRY_DB_FN   = "speech_entry_seen_db"

DATE_HDR_TMPL = "%s"
FEED_HDR_TMPL = "%(feed.title)s\n%(time)s"
ENTRY_TMPL    = "%(entry.title)s\n\n%(entry.summary)s\n%(content)s"
PAGE_TMPL     = "%s"

def main(): 
    """
    Poll subscribed feeds and produce aggregator page.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    if len(entries) > 0:
        # Ensure that the summary and content of entries are
        # stripped of HTML
        s = HTMLStripper()
        for e in entries:
            e.entry.summary = s.strip_html(e.entry.summary)
            if e.entry.has_key("content"):
                e.entry.content[0].value = \
                        s.strip_html(e.entry.content[0].value)
        
        # Write out the text script from new entries, then read into a 
        # sound file.  When done reading, convert to MP3 and import into
        # iTunes and iPod.
        writeAggregatorPage(entries, TXT_FN, DATE_HDR_TMPL, FEED_HDR_TMPL, 
            ENTRY_TMPL, PAGE_TMPL)
        speakTextIntoSoundFile(TXT_FN, SOUND_FN)
        importSoundFile(SOUND_FN)
    
    closeDBs(feed_db, entry_db)

def speakTextIntoSoundFile(txt_fn, sound_fn):
    """
    Use Mac OS X text-to-speech to make a speech recording of a 
    given text file
    """
    print "Reciting text '%s' to file '%s'..." % (txt_fn, sound_fn)
    say_cmd = "/usr/bin/say -o '%s' -f '%s'" % (sound_fn, txt_fn)
    p = os.popen(say_cmd, "w")
    p.close()

IMPORT_APPLESCRIPT = """
property arguments : "%s"

-- Derive a Mac-style path from a given POSIX path.
set track_path to arguments
set track_file to POSIX file track_path

-- Launch iTunes as hidden, if not already running.
tell application "System Events"
	if not (exists process "iTunes") then
		tell application "iTunes"
			launch
			set visible of front window to false
		end tell
	end if
end tell

tell application "iTunes"
	-- Convert the AIFF track (which might take awhile)
	with timeout of 300000 seconds
        set converted_track to item 1 of (convert track_file)
    end timeout

    -- Set the track genre
    set the genre of converted_track to "Speech"
	
	-- This might fail if no iPod is connected, but try to copy converted track.
	try
		set the_iPod to some source whose kind is iPod
		duplicate converted_track to playlist 1 of the_iPod
	end try
end tell
"""
def importSoundFile(sound_fn):
    """
    Given a sound filename, import into iTunes and an iPod.
    """
    print "Converting and importing sound file '%s' into iTunes and iPod..." % sound_fn
    f = os.popen('/usr/bin/osascript', "w")
    f.write(IMPORT_APPLESCRIPT % os.path.abspath(sound_fn))
    f.close()

class HTMLStripper(HTMLParser):
    """
    Parses HTML to extract the page title and description.
    """
    CHUNKSIZE = 1024
    
    def strip_html(self, data):
        self.reset()
        self.feed(data)
        return self.data
    
    def reset(self):
        HTMLParser.reset(self)
        self.data = ""

    def handle_data(self, data): 
        self.data += data
    def handle_entityref(self, data): 
        self.data += ' '
    handle_charref = handle_entityref

if __name__ == "__main__": main()
