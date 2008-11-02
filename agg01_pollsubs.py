#!/usr/bin/env python
"""
agg01_pollsubs.py

Poll subscriptions and create an aggregate page.
"""
import sys, time, feedparser

FEEDS_FN    = "feeds.txt"
HTML_FN     = "aggregator.html"
UNICODE_ENC = "utf-8"

def main(): 
    """
    Poll subscribed feeds and produce aggregator page.
    """
    feeds = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    entries = getFeedEntries(feeds)
    writeAggregatorPage(entries, HTML_FN)

def getFeedEntries(feeds):
    """
    Given a list of feeds, poll each feed and collect entries found, wrapping
    each in an EntryWrapper object.  Sort the entries, then return the list.
    """
    entries = []
    for uri in feeds:
        print "Polling %s" % uri
        try:
            data = feedparser.parse(uri)
            entries.extend([ EntryWrapper(data, e) for e in data.entries ])
        except:
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
