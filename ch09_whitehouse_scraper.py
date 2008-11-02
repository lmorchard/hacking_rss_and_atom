#!/usr/bin/env python
"""
ch09_whitehouse_scraper.py

Use XPathScraper to produce a feed from White House news
"""
import sys
from scraperlib import XPathScraper

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = WhitehouseScraper()
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class WhitehouseScraper(XPathScraper):
    """
    Parses HTML to extract the page title and description.
    """
    # Filename of state database
    STATE_FN = "whitehouse_scraper_state"

    # URL to the Library of Congress news page.
    SCRAPE_URL = "http://www.whitehouse.gov/"

    # Base HREF for all links on the page
    BASE_HREF  = "http://www.whitehouse.gov/"

    # Metadata for scraped feed
    FEED_META = {
        'feed.title'        : 'News from The White House',
        'feed.link'         : SCRAPE_URL,
        'feed.tagline'      : 'News releases scraped from whitehouse.gov',
        'feed.author.name'  : 'The White House',
        'feed.author.email' : 'info@whitehouse.gov',
        'feed.author.url'   : SCRAPE_URL,
    }

    # XPaths for extracting content from the page
    ENTRIES_XPATH = "//xhtml:b/xhtml:a[contains(@href,'/news/releases')]"
    ENTRY_XPATHS = {
        'title'   : './text()',
        'link'    : './@href',
        'summary' : '../../../xhtml:font[2]/text()'
    }

if __name__=="__main__": main()
