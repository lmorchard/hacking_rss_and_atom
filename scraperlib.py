"""
scraperlib

Useful base classes and utilities for HTML page scrapers.
"""
import sys, time, re, shelve, popen2, calendar, md5
from urllib import quote
from urllib2 import urlopen
from urlparse import urljoin, urlparse
from xml.sax.saxutils import escape
from HTMLParser import HTMLParser, HTMLParseError

UNICODE_ENC = "UTF-8"

class FeedEntryDict:
    """
    This class is a wrapper around HTMLMetaDoc objects meant to 
    facilitate easy use in XML template strings.
    """
    UNICODE_ENC = "UTF-8"
    DATE_KEYS   = [ 'modified', 'issued' ]
    
    def __init__(self, init_dict={}, date_fmt='%Y-%m-%dT%H:%M:%SZ'):
        """
        Initialize the feed entry dict, with optional data.
        """
        self.data = {}
        self.data.update(init_dict)
        self.date_fmt = date_fmt
       
    def __cmp__(self, other):
        """Reverse chronological order on modified date"""
        return cmp(other.data['modified'], self.data['modified'])

    def __setitem__(self, name, val):
        """Set a value in the feed entry dict."""
        self.data[name] = val
        
    def __getitem__(self, name):
        """Return a dict item, escaped and encoded for XML inclusion"""
        # Chop off the entry. prefix, if found.
        if name.startswith('entry.'): 
            name = name[6:]
         
        # If this key is a date, format accordingly.
        if name in self.DATE_KEYS:
            date = self.data.get(name, time.time())
            val  = time.strftime(self.date_fmt, time.gmtime(date))

        # Otherwise, try returning what was asked for.
        else: 
            val = self.data.get(name, '')
        
        # Make sure the value is finally safe for inclusion in XML
        if type(val) is unicode:
            val = val.encode(self.UNICODE_ENC)
        return escape(val.strip())
    
    def id(self):
        """Come up with a state DB ID for this entry."""
        # Try to use entry GUID, first.
        id = self['id']
        
        # If no GUID available, hash entry contents.
        if not len(id) > 0:
            m = md5.md5()
            for v in self.data.values():
                if type(v) is unicode:
                    v = v.encode(self.UNICODE_ENC)
                m.update('%s' % v)
            id = m.hexdigest()
            
        return id

class _ScraperFinishedException(Exception):
    """
    Private exception, raised when the scraper has seen all it's 
    interested in parsing.
    """
    pass

ATOM_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"

ATOM_FEED_TMPL = """<?xml version="1.0" encoding="utf-8"?>
<feed version="0.3" xmlns="http://purl.org/atom/ns#">
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
        <summary type="text/html" 
                 mode="escaped">%(entry.summary)s</summary>
    </entry>
"""
RSS_DATE_FMT = "%a, %d %b %Y %H:%M:%S %z"

RSS_FEED_TMPL = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
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
            <description>%(entry.summary)s</description>
        </item>
"""

class Scraper:
    """
     class containing a few methods universal to scrapers.
    """
    UNICODE_ENC = "UTF-8"
    FEED_META = {
        'feed.title'        : 'A Sample Feed',
        'feed.link'         : 'http://www.example.com',
        'feed.tagline'      : 'This is a testing sample feed.',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
        'feed.modified'     : ''
    }
    SORT_ENTRIES = True
    MAX_ENTRIES  = 15
    BASE_HREF    = ""
    SCRAPE_URL   = ""

    ATOM_DATE_FMT   = ATOM_DATE_FMT
    ATOM_FEED_TMPL  = ATOM_FEED_TMPL
    ATOM_ENTRY_TMPL = ATOM_ENTRY_TMPL

    RSS_DATE_FMT    = RSS_DATE_FMT
    RSS_FEED_TMPL   = RSS_FEED_TMPL
    RSS_ENTRY_TMPL  = RSS_ENTRY_TMPL
    
    def scrape_atom(self):
        """Scrape the page and return an Atom feed."""
        self.FEED_META['feed.modified'] = \
            time.strftime(self.ATOM_DATE_FMT, time.gmtime(time.time()))
        return self.scrape(self.ATOM_ENTRY_TMPL, 
                self.ATOM_FEED_TMPL, self.ATOM_DATE_FMT)
        
    def scrape_rss(self):
        """Scrape the page and return an RSS feed."""
        return self.scrape(self.RSS_ENTRY_TMPL, 
                self.RSS_FEED_TMPL, self.RSS_DATE_FMT)
        
    def scrape(self, entry_tmpl, feed_tmpl, date_fmt):
        """
        Given an entry and feed string templates, scrape an HTML page for 
        content and use the templates to return a feed.
        """
        self.date_fmt = date_fmt
        self.state_db = shelve.open(self.STATE_FN)

        # Scrape the source data for FeedEntryDict instances
        entries = self.produce_entries()
        
        # Make a polishing-up run through the extracted entries.
        for e in entries:

            # Come up with ID for state db
            state_id = e.id()
            
            # Make sure the entry link is absolute
            if e.data.has_key('link'):
                e['link'] = urljoin(self.BASE_HREF, e['link'])
            
            # Try to get state for this ID, creating a new record
            # if needed.
            if not self.state_db.has_key(state_id): 
                self.state_db[state_id] = {}
            entry_state = self.state_db[state_id]
            
            # Manage remembered values for datestamps when entry data 
            # first found, unless dates were extracted.
            if e.data.get('modified','') == '':
                if not entry_state.has_key('modified'): 
                    entry_state['modified'] = time.time()
                e.data['modified'] = entry_state['modified']
            
            if e.data.get('issued','') == '':
                e.data['issued'] = e.data['modified']
                
            for n in ('issued', 'modified'):
                if e.data.get(n, '') != '': 
                    continue
            
            # Construct a canonical tag URI for the entry if none set
            if not len(e.data.get('id', '')) > 0:
                (scheme, addr, path, params, query, frag) = \
                    urlparse(e['link'])
                now = e.data.has_key('modified') and time.gmtime(e.data['modified']) or time.gmtime()
                ymd = time.strftime("%Y-%m-%d", now)
                e['id'] = "tag:%s,%s:%s" % (addr, ymd, quote(path,''))
                
            # Update the state database record
            self.state_db[state_id] = entry_state

        # Close the state database
        self.state_db.close()
                    
        # Sort the entries, now that they all should have dates.
        if self.SORT_ENTRIES: entries.sort()
        
        # Build the entries from template, and populate the feed data
        entries_out = [entry_tmpl % e for e in entries[:self.MAX_ENTRIES]]
        feed = { 'feed.entries' : "\n".join(entries_out) }

        # Add all the feed metadata into the feed, ensuring 
        # Unicode encoding happens.
        for k, v in self.FEED_META.items():
            if type(v) is unicode:
                v = v.encode(self.UNICODE_ENC)
            feed[k] = v
        
        # Return the built feed
        return feed_tmpl % feed
    
class RegexScraper(Scraper):
    """
    Base class for regex-based feed scrapers.
    """
    # Default regex extracts all hyperlinks.
    ENTRY_RE = """(?P<summary><a href="(?P<link>.*?)">(?P<title>.*?)</a>)"""

    def __init__(self):
        """Initialize the scraper, compile the regex"""
        self.entry_re = re.compile(self.ENTRY_RE, 
            re.DOTALL | re.MULTILINE | re.IGNORECASE)

    def produce_entries(self):
        """Use regex to extract entries from source"""
        # Fetch the source for scraping.
        src = urlopen(self.SCRAPE_URL).read()

        # Iterate through all the matches of the regex found.
        entries, pos = [], 0
        while True:
            
            # Find the latest match, stop if none found.
            m = self.entry_re.search(src, pos)
            if not m: break
            
            # Advance the search position to end of previous search.
            pos = m.end()
            
            # Create and append the FeedEntryDict for this extraction.
            entries.append(FeedEntryDict(m.groupdict(), self.date_fmt))
        
        return entries

from tidylib import tidy_string
from Ft.Xml.Domlette import NonvalidatingReader

class XPathScraper(Scraper):
    """
    Base class for XPath-based feed scrapers.
    """
    NSS = { 'xhtml':'http://www.w3.org/1999/xhtml' }
    
    # Default xpaths extract all hyperlinks.
    ENTRIES_XPATH = "//xhtml:a"
    ENTRY_XPATHS = {
        'title'   : './text()',
        'link'    : './@href',
        'summary' : './text()'
    }
    
    def produce_entries(self):
        """Use xpaths to extract feed entries and entry attributes."""
        # Fetch the HTML source, tidy it up, parse it.
        src      = urlopen(self.SCRAPE_URL).read()
        tidy_src = tidy_string(src)
        doc      = NonvalidatingReader.parseString(tidy_src, self.SCRAPE_URL)

        entries = []

        # Iterate through the parts identified as feed entry nodes.
        for entry_node in doc.xpath(self.ENTRIES_XPATH, self.NSS):

            # For each entry attribute path, attempt to extract the value
            data = {}
            for k,v in self.ENTRY_XPATHS.items():
                nodes   = entry_node.xpath(v, self.NSS)
                vals    = [x.nodeValue for x in nodes if x.nodeValue]
                data[k] = " ".join(vals)
                
            # Create and append the FeedEntryDict for this extraction
            entries.append(FeedEntryDict(data, self.date_fmt))
        
        return entries
    
class HTMLScraper(HTMLParser, Scraper):
    """
    Base class for HTMLParser-based feed scrapers.
    """
    CHUNKSIZE   = 1024

    def produce_entries(self):
        fin = urlopen(self.SCRAPE_URL)
        return self.parse_file(fin)
        
    def reset(self):
        """Initialize the parser state."""
        HTMLParser.reset(self)
        self.feed_entries = []
        self.in_feed      = False
        self.in_entry     = False
        self.curr_data    = ''
    
    def start_feed(self):
        """Handle start of feed scraping"""
        self.in_feed = True

    def end_feed(self):
        """Handle end of all useful feed scraping."""
        raise _ScraperFinishedException()
            
    def start_feed_entry(self):
        """Handle start of feed entry scraping"""
        self.curr_entry = FeedEntryDict({}, self.date_fmt)
        self.in_entry   = True

    def end_feed_entry(self):
        """Handle the detected end of a feed entry scraped"""
        self.feed_entries.append(self.curr_entry)
        self.in_entry = False
    
    def handle_data(self, data):
        self.curr_data += data
    def handle_entityref(self, data): 
        self.curr_data += '&' + data + ';'
    handle_charref = handle_entityref

    def decode_entities(self, data):
        data = data.replace('&lt;', '<')
        data = data.replace('&gt;', '>')
        data = data.replace('&quot;', '"')
        data = data.replace('&apos;', "'")
        data = data.replace('&amp;', '&')
        return data
    
    def parse_file(self, fin):
        """Parse through the contents of a given file-like object."""
        self.reset()
        while True:
            try:
                data = fin.read(self.CHUNKSIZE)
                if len(data) == 0: break
                self.feed(data)
            except _ScraperFinishedException:
                break
        return self.feed_entries
           
