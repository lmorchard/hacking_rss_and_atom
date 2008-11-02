#!/usr/bin/env python
"""
ch09_loc_scraper.py

Use HTMLScraper to produce a feed from loc.gov news
"""
import sys, time, shelve
from urlparse import urljoin
from scraperlib import HTMLScraper

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed from the loc.gov news page.
    """
    scraper = LOCScraper()
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class LOCScraper(HTMLScraper):
    """
    Parses HTML to extract the page title and description.
    """
    # Filename of state database
    STATE_FN   = "loc_scraper_state"

    # URL to the Library of Congress news page.
    SCRAPE_URL = "http://www.loc.gov/today/pr/"

    # Base HREF for all links on the page
    BASE_HREF  = SCRAPE_URL

    # Metadata for scraped feed
    FEED_META = {
        'feed.title'        : 'News from The Library of Congress',
        'feed.link'         : SCRAPE_URL,
        'feed.tagline'      : 'Press releases scraped from loc.gov',
        'feed.author.name'  : 'Library of Congress',
        'feed.author.email' : 'pao@loc.gov',
        'feed.author.url'   : SCRAPE_URL,
    }

    def reset(self):
        """Reset scraper before next run."""
        HTMLScraper.reset(self)
        
    def handle_comment(self, data):
        """Look for HTML comments that mark start & end of extraction"""
        if 'START PR LIST' in data: self.start_feed()
        if 'END BODY TABLE' in data: self.end_feed()
        
    def handle_starttag(self, tag, attrs_tup):
        """Handle start tags."""
        attrs = dict(attrs_tup)
       
        # Use <base> to get the correct base HREF
        if tag == 'base':
            self.base_href = attrs['href']
            
        # Use <dl> as signal of entry start.
        if self.in_feed:
            if tag == 'dl':
                self.start_feed_entry()
                
        # Harvest links from <a href="">
        if self.in_entry:
            if tag == "a":
                self.curr_entry['link'] = attrs.get("href", "")
                    
    def handle_endtag(self, tag):
        """Handle end tags."""
        
        # If started scraping a feed...
        if self.in_feed:
            # ...</dl> ends it.
            if tag == 'dl':
                self.end_feed_entry()
         
        # If in an entry...
        if self.in_entry:
            # ...the end of </a> provides title string.
            if tag == "a":
                self.curr_entry['title'] = self.curr_data.strip()
            
            # ...accumulate plain text data for the summary.
            self.curr_entry['summary'] += self.curr_data
        
        # Clear the tag character data accumulation.
        self.curr_data   = ''
        
if __name__=="__main__": main()
