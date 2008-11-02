#!/usr/bin/env python
"""
ch09_fcc_scraper.py

Use RegexScraper to produce a feed from fcc.gov news
"""
import sys, time, shelve, md5, re
from urlparse import urljoin
from scraperlib import RegexScraper

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = FCCScraper()
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class FCCScraper(RegexScraper):
    """Use regexes to scrape FCC news headlines"""
    
    # Filename of state database
    STATE_FN   = "fcc_scraper_state"

    # URL to the Library of Congress news page.
    SCRAPE_URL = "http://www.fcc.gov/headlines.html"

    # Base HREF for all links on the page
    BASE_HREF  = SCRAPE_URL
    
    # Metadata for scraped feed
    FEED_META = {
        'feed.title'        : 'FCC News',
        'feed.link'         : SCRAPE_URL,
        'feed.tagline'      : 'News from the FCC',
        'feed.author.name'  : 'Federal Communications Commission',
        'feed.author.email' : 'fccinfo@fcc.gov',
        'feed.author.url'   : 'http://www.fcc.gov/aboutus.html'
    }

    # Regex to extract news headline paragraphs
    ENTRY_RE = '<p>' + \
        '<span class="headlinedate">(?P<date>.*?)</span>.*?<br>' + \
        '(?P<title>.*?)<br>' + \
        '(?P<summary>.*?)' + \
        '</p>'

    HTML_RE = re.compile('<(.*?)>')
            
    def produce_entries(self):
        """Parse and generate dates extracted from HTML content"""
        # Extract entries using superclass method
        entries = RegexScraper.produce_entries(self)

        # Finish up entries extracted
        for e in entries:

            # Delete all HTML tags from the title attribute
            e.data['title'] = self.HTML_RE.sub('', e.data['title'])
            
            # Turn the extracted date into proper issued / modified dates
            dp   = [int(x) for x in e['date'].split('/')]
            dtup = (2000+dp[2], dp[0], dp[1], 0, 0, 0, 0, 0, 0)
            date = time.mktime(dtup)
            e['issued']   = date
            e['modified'] = date

            # Create an ID for the extracted entry
            m = md5.md5()
            m.update(e['title'])
            ymd = time.strftime("%Y-%m-%d", time.gmtime(date))
            e['id'] = "tag:www.fcc.gov,%s:%s" % (ymd, m.hexdigest())
        
        # Return the list of entries.
        return entries

if __name__=="__main__": main()
