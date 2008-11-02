#!/usr/bin/env python
"""
agg02_pollsubs.py

Poll subscriptions and create an aggregate page, keeping track
of feed changes and new/old items.
"""
import sys, time, feedparser, shelve, md5, time

FEEDS_FN    = "feeds.txt"
HTML_FN     = "aggregator-%s.html"
UNICODE_ENC = "utf-8"

FEED_DB_FN  = "feeds_db"
ENTRY_DB_FN = "entry_seen_db"

def main(): 
    """
    Poll subscribed feeds and produce aggregator page.
    """
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)

    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    if len(entries) > 0:
        out_fn = HTML_FN % time.strftime("%Y%m%d-%H%M%S")
        writeAggregatorPage(entries, out_fn)
    
    closeDBs(feed_db, entry_db)

def openDBs(feed_db_fn, entry_db_fn):
    """
    Open the databases used to track feeds and entries seen.
    """
    feed_db  = shelve.open(feed_db_fn)
    entry_db = shelve.open(entry_db_fn)
    return (feed_db, entry_db)

def closeDBs(feed_db, entry_db):
    """
    Close the databases used to track feeds and entries seen.
    """
    feed_db.close()
    entry_db.close()

def getNewFeedEntries(feeds, feed_db, entry_db):
    """
    Given a list of feeds, poll feeds which have not been polled in over
    an hour.  Look out for conditional HTTP GET status codes before 
    processing feed data.  Check if we've seen each entry in a feed,
    collecting any entries that are new.  Sort the entries, then return 
    the list.
    """
    entries = []
    for uri in feeds:
        print "Polling %s" % uri
        try:
            # Get the notes rememebered for this feed.
            feed_data = feed_db.get(uri, {})
            last_poll = feed_data.get('last_poll', None)
            etag      = feed_data.get('etag', None)
            modified  = feed_data.get('modified', None)
            
            # Check to see whether it's time to poll this feed yet.
            if last_poll and (time.time() - last_poll) < 3600:
                print "\tFeed already polled within the last hour."
            
            else:
                # Fetch the feed using the ETag and Last-Modified notes.
                feed_data = feedparser.parse(uri,etag=etag,modified=modified)
                
                # If the feed HTTP status is 304, there was no change.
                if feed_data.status == 304:
                    print "\tFeed unchanged."
                
                else:
                    new_entries = 0
                    
                    for entry_data in feed_data.entries:
                    
                        # Wrap the entry data and get a hash for the entry.
                        entry = EntryWrapper(feed_data, entry_data)
                        hash  = entry.hash()
                        
                        # If the hash for this entry is found in the DB, 
                        # it's not new.
                        if entry_db.has_key(hash): continue

                        # Flag entry as seen with the hash key, append to 
                        # list of new entries.
                        entry_db[hash] = 1
                        entries.append(entry)
                        new_entries += 1
                    
                    print "\tFound %s new entries" % new_entries

            # Finally, update the notes remembered for this feed.
            feed_db[uri] = {
                'last_poll' : time.time(),
                'etag'      : feed_data.get('etag', None),
                'modified'  : feed_data.get('modified', None)
            }
            
        except:
            raise
            print "Problem polling %s" % uri
    
    entries.sort()
    return entries
    
def writeAggregatorPage(entries, out_fn):
    """
    Given a list of entries and an output filename, use templates to compose
    an aggregate page from the feeds and write to the file.
    """
    out, curr_day, curr_feed = [], None, None

    for e in entries:
        # If this entry's date is not the current running day, change the 
        # current day and add a date header to the page output.
        if e['date'] != curr_day:
            curr_day = e['date']
            out.append(DATE_HDR_TMPL % curr_day)
            
            # Oh yeah, and output a reminder of the current feed after the
            # day header if it hasn't changed.
            if e.feed.title == curr_feed:
                out.append(FEED_HDR_TMPL % e)
        
        # If this entry's feed isn't the current running feed, change the
        # current feed and add a feed header to the page output.
        if e.feed.title != curr_feed:
            curr_feed = e.feed.title
            out.append(FEED_HDR_TMPL % e)
        
        # Add the entry to the page output.
        out.append(ENTRY_TMPL % e)

    # Concatenate all the page output collected, fill the page templage, and
    # write the result to the output file.
    open(out_fn, "w").write(PAGE_TMPL % "".join(out))

class EntryWrapper:
    def __init__(self, data, entry): 
        """
        Initialize the wrapper with feed and entry data.
        """
        self.data  = data
        self.feed  = data.feed
        self.entry = entry
        
        # Try to work out some sensible primary date for the entry, fall
        # back to the feed's date, and use the current time as a last resort.
        if entry.has_key("modified_parsed"):
            self.date = time.mktime(entry.modified_parsed)
        elif entry.has_key("issued_parsed"):
            self.date = time.mktime(entry.issued_parsed)
        elif self.feed.has_key("modified_parsed"):
            self.date = time.mktime(self.feed.modified_parsed)
        elif self.feed.has_key("issued_parsed"):
            self.date = time.mktime(self.feed.issued_parsed)
        else:
            self.date = time.time()

    def __cmp__(self, other):
        """
        Use the entry's date as the comparator for sorting & etc.
        """
        return other.date - self.date
    
    def __getitem__(self, name):
        """
        """
        # Handle access to feed data on keys starting with "feed."
        if name.startswith("feed."):
            return self.feed.get(name[5:], "").encode(UNICODE_ENC)
        # Handle access to entry data on keys starting with "entry."
        if name.startswith("entry."):
            return self.entry.get(name[6:], "").encode(UNICODE_ENC)
        # Handle a few more special-case keys.
        if name == "date":
            return time.strftime("%Y-%m-%d", time.localtime(self.date))
        if name == "time": 
            return time.strftime("%H:%M:%S", time.localtime(self.date))
        if name == "content":
            if self.entry.has_key("content"):
                return self.entry.content[0].value.encode(UNICODE_ENC)
            return ""

        # If all else fails, return an empty string.
        return ""
    
    def hash(self):
        """
        Come up with a unique identifier for this entry.
        """
        if self.entry.has_key('id'):
            return self.entry['id'].encode(UNICODE_ENC)
        else:
            m = md5.md5()
            for k in ('title', 'link', 'issued', 'modified', 'description'):
                m.update(self.entry.get(k,'').encode(UNICODE_ENC))
            return m.hexdigest()


# Presentation templates for output follow:

DATE_HDR_TMPL = """
    <h1 class="dateheader">%s</h1>
"""

FEED_HDR_TMPL = """
    <h2 class="feedheader"><a href="%(feed.link)s">%(feed.title)s</a></h2>
"""

ENTRY_TMPL = """
    <div class="feedentry">
        <div class="entryheader">
            <span class="entrytime">%(time)s</span>: 
            <a class="entrylink" href="%(entry.link)s">%(entry.title)s</a>
        </div>
        <div class="entrysummary">
            %(entry.summary)s
            <hr>
            %(content)s
        </div>
    </div>
"""

PAGE_TMPL = """
<html>
    <head>
        <style>
            body {
                font-family: sans-serif;
                font-size: 12px;
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
        <h1 class="pageheader">Feed aggregator #1</h1>
        %s
    </body>
</html>
"""

if __name__ == "__main__": main()
