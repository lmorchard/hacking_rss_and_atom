#!/usr/bin/env python
"""
ch11_svn_log_scraper.py

Scrape a feed from log events for a Subversion repository
"""
import sys, time, calendar
from urllib import quote
from urlparse import urljoin, urlparse
from popen2 import popen4
from Ft.Xml.Domlette import NonvalidatingReader
from scraperlib import FeedEntryDict, Scraper

SVN_TITLE = "Colloquy"
SVN_URL   = 'http://source.colloquy.info/colloquy/'

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.  Also optionally accepts a URL to a 
    Subversion repository.
    """
    svn_title = (len(sys.argv) > 2) and sys.argv[2] or SVN_TITLE
    svn_uri   = (len(sys.argv) > 3) and sys.argv[3] or SVN_URL
    scraper   = SVNScraper(svn_uri)
    
    scraper.FEED_META['feed.title'] = \
        "Subversion history for %s" % svn_title
    scraper.FEED_META['feed.link']  = svn_uri
     
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class SVNScraper(Scraper):
    """
    Base class for XPath-based feed scrapers.
    """
    SVN_BIN    = '/sw/bin/svn'
    TAG_PREFIX = 'colloquy.info,2005-03-12:'
    LOG_PERIOD = 7 * 24 * 60 * 60 # (1 week)
    STATE_FN   = 'svn_scraper'
    
    def __init__(self, url):
        """Initialize with URL to Subversion repository"""
        self.url = url
        
        # Come up with a tag prefix based in svn URL and current time
        (scheme, addr, path, params, query, frag) = urlparse(url)
        ymd = time.strftime("%Y-%m-%d", time.gmtime())
        self.TAG_PREFIX = "%s,%s:" % (addr, ymd)
    
    def produce_entries(self):
        """Use xpaths to extract feed entries and entry attributes."""
        entries = []

        # Iterate through the parts identified as log entry nodes.
        for entry_node in self.svn_log().xpath('//logentry'):

            # Extract a few basic elements from the log entry
            revision = self.xpval(entry_node, './@revision')
            author   = self.xpval(entry_node, './author/text()')
            msg      = self.xpval(entry_node, './msg/text()')
            
            # Extract and parse the date for the log entry
            date_str   = self.xpval(entry_node, './date/text()')
            date_tup   = time.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
            entry_time = calendar.timegm(date_tup)

            # Extract and process the list of affected file paths
            paths_changed = []
            for path_node in entry_node.xpath('./paths/path'):
                action = self.xpval(path_node, './@action')
                path   = self.xpval(path_node, './text()')
                paths_changed.append("%s %s" % (action, path))
            
            entry_id = 'tag:%s%s' % (self.TAG_PREFIX, revision)

            # Build the feed entry based on log entry information
            entry = FeedEntryDict(init_dict={
                'id'        : entry_id,
                'title'     : 'Revision %s by %s' % (revision, author),
                'link'      : self.url,
                'issued'    : entry_time,
                'modified'  : entry_time,
                'summary'   : "<pre>%s\n\nFiles affected:\n%s</pre>" % 
                              (msg, '\n'.join(paths_changed))
                    
            }, date_fmt=self.date_fmt)
            entries.append(entry)
        
        return entries
    
    def svn_log(self):
        """
        Make a log query to the Subversion repository, 
        return parsed XML document of query output.
        """
        # Calculate the start and end times for log query
        now  = time.time()
        then = now - self.LOG_PERIOD
        
        # Format the start/end times for use in svn command
        start_time = time.strftime("%Y-%m-%d", time.localtime(then))
        end_time   = time.strftime("%Y-%m-%d", time.localtime(now))

        # Build the svn command invocation, execute it, and return
        # the XML results in a parsed document.
        cmd = '%s log --xml -v -r "{%s}:{%s}" %s' % \
            (self.SVN_BIN, start_time, end_time, self.url)
        (sout, sin) = popen4(cmd)
        return NonvalidatingReader.parseStream(sout, self.url)

    def xpval(self, node, xpath):
        """Given a node and an xpath, extract all text information"""
        vals = [x.nodeValue for x in node.xpath(xpath) if x.nodeValue]
        return " ".join(vals)
    
if __name__ == '__main__': main()

