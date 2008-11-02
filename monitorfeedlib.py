#!/usr/bin/env python
"""
monitorfeedlib.py

Utilities for building feeds from system logs and reports.
"""
import sys, os, os.path, time, md5, difflib, gzip
from cPickle import dump, load
from scraperlib import FeedEntryDict, Scraper

def main():
    """
    Test out LogBufferFeed by maintaining a random number feed.
    """
    # Construct the feed generator
    f = LogBufferFeed('random_feed')
    f.FEED_META['feed.title']   = 'Random Number of the Moment'
    f.FEED_META['feed.tagline'] = 'Serving your random number needs.'
    f.MAX_ENTRIES = 4
    f.MAX_AGE     = 30 #10 * 60 # 10 minutes
    
    # Construct and append a new entry
    import random
    num = random.random() * 1000
    entry = FeedEntryDict({
        'title'   : 'Random number %s' % num,
        'link'    : '',
        'summary' : 'Here is another random number for you: %s' % num
    })
    f.append_entry(entry)

    # Output the current feed entries
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print f.scrape_rss()
    else:
        print f.scrape_atom()

class LogBufferFeed(Scraper):
    """
    Implements a log-style buffered feed, where new entries can be added
    and kept in the feed until they become stale.  Generated feeds will
    include buffered entries from previous program runs.
    """
    TAG_DOMAIN  = 'decafbad.com'
    MAX_ENTRIES = 50
    MAX_AGE     = 4 * 60 * 6 # 4 hours
    
    def __init__(self, entries_dir):
        """Initialize object with the path to pickled entries."""
        if not os.path.exists(entries_dir): os.makedirs(entries_dir)
        self.entries_dir = entries_dir
        self.STATE_FN    = os.path.join(entries_dir, 'state')

    def produce_entries(self):
        """Load up entries and fix up before producing feed."""
        # Load up all the pickled entries
        entries = [ load(open(x, 'rb')) for x in self.get_entry_paths() ]
        
        # Tweak each loaded entry to use proper date format.
        for entry in entries:
            entry.date_fmt = self.date_fmt

        # Return the fixed entries.
        return entries

    def append_entry(self, entry):
        """Add a given entry to the buffer."""
        # Clean up entries before adding a new one.
        self.clean_entries()

        # Update entry's modified timestamp.
        entry['modified'] = time.time()

        # Build an ID for this new entry.
        hash = self.hash_entry(entry)
        ymd  = time.strftime("%Y-%m-%d", time.gmtime())
        entry['id'] = "tag:%s,%s:%s.%s" % \
            (self.TAG_DOMAIN, ymd, self.entries_dir, hash)

        # Build entry's file path based on a hash.
        entry_fn   = "entry-%s" % hash
        entry_path = os.path.join(self.entries_dir, entry_fn)
        
        # Pickle the entry out to a file.
        dump(entry, open(entry_path, 'wb'))

    def clean_entries(self):
        """Delete entries older than the maximum age."""
        # Get entry file paths and iterate through them.
        entry_paths = self.get_entry_paths()
        for entry_path in entry_paths:
            
            # Load up the current entry.
            entry = load(open(entry_path, "rb"))
            
            # Delete the entry if it's gotten too old.
            entry_age = time.time() - entry.data['modified']
            if entry_age > self.MAX_AGE:
                os.unlink(entry_path)

    def get_entry_paths(self):
        """Get paths to all the pickled entry files."""
        return [ os.path.join(self.entries_dir, x)
                 for x in os.listdir(self.entries_dir) 
                 if x.startswith('entry-') ]

    def hash_entry(self, entry):
        """Produce a filename-safe hash of an entry's contents."""
        m = md5.md5()
        for k in entry.data.keys():
            v = entry.data[k]
            if not type(v) is unicode:
                m.update('%s' % v)
            else:
                m.update(v.encode(entry.UNICODE_ENC))
        return m.hexdigest()

if __name__ == '__main__': main()
