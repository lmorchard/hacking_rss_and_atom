"""
ch15_bayes_agg.py

Bayes-enabled feed aggregator
"""
import sys, time, md5, urllib
import feedparser
from agglib import UNICODE_ENC, EntryWrapper, openDBs, closeDBs
from agglib import getNewFeedEntries, writeAggregatorPage
from reverend.thomas import Bayes

FEEDS_FN        = "bayes_feeds.txt"
FEED_DB_FN      = "bayes_feeds_db"
ENTRY_DB_FN     = "bayes_entry_seen_db"
HTML_FN         = "bayes-agg-%Y%m%d-%H%M%S.html"
BAYES_DATA_FN   = "bayesdata.dat"
ENTRY_UNIQ_KEYS = ('title', 'link', 'issued', 
                   'modified', 'description')

def main():
    """
    Build aggregator report pages with Bayes rating links.
    """
    # Create a new Bayes guesser
    guesser = Bayes()

    # Attempt to load Bayes data, ignoring IOError on first run.
    try: guesser.load(BAYES_DATA_FN)
    except IOError: pass
    
    # Open up the databases, load the subscriptions, get new entries.
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)
    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    # Score the new entries using the Bayesian guesser
    entries = scoreEntries(guesser, entries)

    # Write out the current run's aggregator report.
    out_fn  = time.strftime(HTML_FN)
    writeAggregatorPage(entries, out_fn, DATE_HDR_TMPL, FEED_HDR_TMPL, 
        ENTRY_TMPL, PAGE_TMPL)
    
    # Close the databases and save the current guesser's state to disk.
    closeDBs(feed_db, entry_db)
    guesser.save(BAYES_DATA_FN)
    
class ScoredEntryWrapper(EntryWrapper):
    """
    Tweak the EntryWrapper class to include a score for the entry.
    """
    def __init__(self, data, entry, score=0.0): 
        EntryWrapper.__init__(self, data, entry)
        self.score = score
        self.id    = makeEntryID(entry)
    
    def __getitem__(self, name):
        """
        Include the entry score & id in template output options.
        """
        # Allow prefix for URL quoting
        if name.startswith("url:"):
            return urllib.quote(self.__getitem__(name[4:]))
        
        if name == 'id':          return self.id
        if name == 'feed.url':    return self.data.url
        if name == 'entry.score': return self.score
        return EntryWrapper.__getitem__(self, name)

def scoreEntries(guesser, entries):
    """
    Return a list of entries modified to include scores.
    """
    return [ ScoredEntryWrapper(e.data, e.entry, scoreEntry(guesser, e))
             for e in entries ]
            
def scoreEntry(guesser, e):
    """
    Score an entry, assuming like and dislike classifications.
    """
    guess = dict( guessEntry(guesser, e) )
    return guess.get('like', 0) - guess.get('dislike', 0)
    
def trainEntry(guesser, pool, e):
    """
    Train classifier for given class, feed, and entry.
    """
    content = summarizeEntry(e)
    guesser.train(pool, content)

def guessEntry(guesser, e):
    """
    Make a classification guess for given feed and entry.
    """
    content = summarizeEntry(e)
    return guesser.guess(content)

def summarizeEntry(e):
    """
    Summarize entry content for use with the Bayes guesser.
    """
    # Include the feed title
    content = [ e.data.feed.title ]
    # Include the entry title and summary
    content.extend([ e.entry.get(x,'') for x in ('title', 'summary' ) ])
    # Include the entry content.
    content.extend([ x.value for x in e.entry.get('content', []) ])
    # Join all the content together with spaces and return.
    return ' '.join(content)

def findEntry(feed_uri, entry_id):
    """
    Attempt to locate a feed entry, given the feed URI and an entry ID.
    """
    feed_data = feedparser.parse(feed_uri)
    for entry in feed_data.entries:
        if makeEntryID(entry) == entry_id:
            return ScoredEntryWrapper(feed_data, entry, 0.0)
    return None

def makeEntryID(entry):
    """Find a unique identifier for a given entry."""
    if entry.has_key('id'):
        # Use the entry's own GUID.
        return entry['id'].encode(UNICODE_ENC)
    else:
        # No entry GUID, so build one from an MD5 hash of select data.
        entry_data = ''.join([
            entry.get(k,'').encode(UNICODE_ENC)
            for k in ENTRY_UNIQ_KEYS
        ])
        return md5.md5(entry_data).hexdigest()

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
            [ %(entry.score)0.3f ]
            [ <a href="javascript:ratepop('ch15_bayes_mark_entry.cgi?feed=%(url:url:feed.url)s&entry=%(url:url:id)s&like=1')">++</a> ]
            [ <a href="javascript:ratepop('ch15_bayes_mark_entry.cgi?feed=%(url:url:feed.url)s&entry=%(url:url:id)s&like=0')">--</a> ]
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
        <script>
            function ratepop(url) {
                window.open(url, 'rating', 'width=550,height=125,location=no,menubar=no,status=no,toolbar=no,scrollbars=no,resizable=yes');
            }
        </script>
    </head>
    <body>
        <h1 class="pageheader">Bayes feed aggregator</h1>
        %s
    </body>
</html>
"""
    
if __name__ == "__main__": main()
