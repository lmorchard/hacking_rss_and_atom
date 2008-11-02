#!/usr/bin/env python
"""
ch15_bayes_filter.py

Build a new feed out of entries filtered from a source feed
above a given Bayesian classifier threshold.
"""
import sys, os, time, ch15_bayes_agg
from agglib import openDBs, closeDBs, getNewFeedEntries
from scraperlib import Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries
from reverend.thomas import Bayes

FEED_TITLE    = 'Bayes Recommendations'
FEED_TAGLINE  = 'Entries recommended by Bayesian-derived ratings'
FEED_NAME_FN  = "www/www.decafbad.com/docs/private-feeds/bayes-filtered.%s"
FEEDS_FN      = "bayes_feeds.txt"
FEED_DB_FN    = "bayes_filter_feeds_db"
ENTRY_DB_FN   = "bayes_filter_entry_seen_db"
BAYES_DATA_FN = "bayesdata.dat"

def main():
    """
    Perform a test run of the FeedFilter using defaults.
    """
    # Create a new Bayes guesser, attempt to load data
    guesser = Bayes()
    guesser.load(BAYES_DATA_FN)
    
    # Open up the databases, load the subscriptions, get new entries.
    feed_db, entry_db = openDBs(FEED_DB_FN, ENTRY_DB_FN)
    feeds   = [ x.strip() for x in open(FEEDS_FN, "r").readlines() ]
    entries = getNewFeedEntries(feeds, feed_db, entry_db)
    
    # Build the feed filter.
    f = BayesFilter(guesser, entries)
    f.FEED_META['feed.title']   = FEED_TITLE
    f.FEED_META['feed.tagline'] = FEED_TAGLINE
    
    # Output the feed as both RSS and Atom.
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())
    
    # Close the databases and save the current guesser's state to disk.
    closeDBs(feed_db, entry_db)
    
class BayesFilter(Scraper):
    """
    Filter feed entries using scores from a Bayesian classifier.
    """
    LAST_RUN_FN  = 'filter_last_run.txt'
    STATE_FN     = 'bayes_filter_state'
    
    def __init__(self, guesser, entries, min_score=0.5):
        """Initialize with the feed URI for parsing."""
        self.guesser          = guesser
        self.entries          = entries
        self.min_score        = min_score
        self.entries_filtered = []

    def produce_entries(self):
        """
        Filter entries from a feed using the regex map, use the
        feed normalizer to produce FeedEntryDict objects.
        """
        # If this hasn't already been done, filter aggregator entries.
        if len(self.entries_filtered) < 1:
            self.filter_aggregator_entries()
            
        # Normalize all the filtered entries
        entries = normalize_entries(self.entries_filtered)
        for e in entries:
            e.date_fmt = self.date_fmt
        
        return entries
    
    def filter_aggregator_entries(self):
        """
        Process new entries from the aggregator for inclusion in the
        output feed.  This is broken out into its own method in order
        to reuse the new entries from the aggregator for multiple feed
        output runs.
        """
        # Now, get a score for each entry and, for each entry scored
        # above the minimum threshold, include it in the entries for output.
        for e in self.entries:
            score = ch15_bayes_agg.scoreEntry(self.guesser, e)
            if score > self.min_score:
                # HACK: Tweak each entry's title to include the score.
                e.entry['title'] = u"(%0.3f) %s" % \
                        (score, e.entry.get('title', 'untitled')) 
                self.entries_filtered.append(e.entry)
        
if __name__=='__main__': main()

