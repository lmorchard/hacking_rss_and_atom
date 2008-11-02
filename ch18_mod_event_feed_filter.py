#!/usr/bin/env python
"""
ch18_mod_event_feed_filter.py

Enhance a feed with metadata harvested from entry content
"""
import sys, feedparser
from scraperlib import FeedEntryDict, Scraper
from ch14_feed_normalizer import normalize_feed_meta, normalize_entries
from hcalendar import HCalendarParser

FEED_IN_URL = 'file://./hcal.atom' 
FEED_OUT_FN = "www/www.decafbad.com/docs/private-feeds/mod-event.%s"

def main():
    """
    Run a feed through the filter and produce the mod_event 
    enhanced version.
    """
    # Grab the incoming feed URL
    feed_url = ( len(sys.argv) > 1 ) and sys.argv[1] or FEED_IN_URL

    f = ModEventFeed(feed_url)
    f.STATE_FN = 'mod_event_feed_filter'
    
    # Output the current feed entries as both RSS and Atom
    open(FEED_OUT_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_OUT_FN % 'atom', 'w').write(f.scrape_atom())
    
class ModEventFeed(Scraper):
    """
    Enhance feed metadata by parsing content.
    """
    ATOM_FEED_TMPL = """<?xml version="1.0" encoding="utf-8"?>
    <feed version="0.3" xmlns="http://purl.org/atom/ns#"
          xmlns:ev="http://purl.org/rss/1.0/modules/event/">
        <title>%(feed.title)s</title>
        <link rel="alternate" type="text/html"
              href="%(feed.link)s" />
        <tagline>%(feed.tagline)s</tagline>
        <modified>%(feed.modified)s</modified>
        <author>
            <name>%(feed.author.name)s</name>
            <email>%(feed.author.email)s</email>
            <url>%(feed.author.url)s</url>
        </author>
        %(feed.entries)s
    </feed>
    """

    ATOM_ENTRY_TMPL = """
        <entry>
            <title>%(entry.title)s</title>
            <link rel="alternate" type="text/html"
                  href="%(entry.link)s" />
            <issued>%(entry.issued)s</issued>
            <modified>%(entry.modified)s</modified>
            <id>%(entry.id)s</id>
            <ev:startdate>%(entry.ev_startdate)s</ev:startdate>
            <ev:enddate>%(entry.ev_enddate)s</ev:enddate>
            <summary type="text/html" 
                     mode="escaped">%(entry.summary)s</summary>
        </entry>
    """

    RSS_FEED_TMPL = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0"
         xmlns:ev="http://purl.org/rss/1.0/modules/event/">
        <channel>
            <title>%(feed.title)s</title>
            <link>%(feed.link)s</link>
            <description>%(feed.tagline)s</description>
            <webMaster>%(feed.author.email)s</webMaster>
            %(feed.entries)s
        </channel>
    </rss>
    """
    
    RSS_ENTRY_TMPL = """
        <item>
            <title>%(entry.title)s</title>
            <link>%(entry.link)s</link>
            <pubDate>%(entry.modified)s</pubDate>
            <guid isPermaLink="false">%(entry.id)s</guid>
            <ev:startdate>%(entry.ev_startdate)s</ev:startdate>
            <ev:enddate>%(entry.ev_enddate)s</ev:enddate>
            <description>%(entry.summary)s</description>
        </item>
    """

    def __init__(self, main_feed):
        """Initialize with the feed URI for parsing."""
        self.main_feed = main_feed

    def produce_entries(self):
        """
        Get a feed, attempt to parse out hCalendar content
        and add mod_event metadata based on it.
        """
        # Grab and parse the feed
        feed = feedparser.parse(self.main_feed)
        
        # Normalize feed meta data
        self.FEED_META = normalize_feed_meta(feed, self.date_fmt)

        # Run through all the normalized entries...
        hp = HCalendarParser()
        entries = normalize_entries(feed.entries)
        for entry in entries:
            events = hp.parse(entry.data['summary'])
            if events:
                event = events[0]

                if 'dtstart' in event:
                    dtstart = event.decoded('dtstart')
                    entry.data['ev_startdate'] = \
                        dtstart.strftime('%Y-%m-%dT%H:%M:%SZ')

                if 'dtend' in event:
                    dtend = event.decoded('dtend')
                    entry.data['ev_enddate'] = \
                        dtend.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        return entries

if __name__=='__main__': main()

