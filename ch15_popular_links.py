#!/usr/bin/env python
"""
ch15_popular_links.py

Build a feed summarizing link popularity found in a set of feeds.
"""
import sys, re, time, calendar, feedparser

from scraperlib import FeedEntryDict
from monitorfeedlib import LogBufferFeed
from HTMLParser import HTMLParser, HTMLParseError

FEED_TITLE     = 'Popular Links'
FEED_TAGLINE   = 'Links found in feed entries ranked by popularity'
FEED_NAME_FN   = "www/www.decafbad.com/docs/private-feeds/popular-links.%s"
FEED_DIR       = 'popular-links-feed'
FEEDS_FN       = 'popular-feed-uris.txt'
MIN_LINKS      = 3
MAX_ENTRY_AGE  = 3 * 24 * 60 * 60

TITLE_TMPL     = """Popular links @ %(time)s (%(link_cnt)s links)"""
TITLE_TIME_FMT = """%Y-%m-%d %H:%M"""

CONTENT_TMPL = """
    <div>
        %s
    </div>
"""
LINK_TMPL = """
    <div style="padding: 10px; margin: 10px; border: 1px solid #aaa;">
        <a style="font-size:1.25em" href="%(link)s">%(link).80s</a><br />
        <i style="font-size:0.75em">(%(link_cnt)s links)</i> 
        <ul>
            %(linkers)s
        </ul>
    </div>
"""
LINKER_TMPL = """
    <li>
        <a href="%(entry.link)s">%(entry.title)s</a>
        <br />
        <span style="font-size:0.75em">
            [ <a href="%(feed.link)s">%(feed.title)s</a> ]
        </span>
    </li>
"""

def main():
    """
    Scan all feeds and update the feed with a new link popularity
    report entry.
    """
    # Construct the feed generator.
    f = LogBufferFeed(FEED_DIR)
    f.MAX_AGE = 1 * 24 * 60 * 60 # 1 day
    f.FEED_META['feed.title']   = FEED_TITLE
    f.FEED_META['feed.tagline'] = FEED_TAGLINE

    # Load up the list of feeds.
    feed_uris  = [ x.strip() for x in open(FEEDS_FN,'r').readlines() ]

    # Skim for links from each feed, collect feed and entries in an
    # inverted index using link URLs as top-level keys.
    links = {}
    for feed_uri in feed_uris:
        feed_data = feedparser.parse(feed_uri)
    
        # Grab the feed metadata from parsed feed.
        feed      = feed_data.feed
        feed_link = feed.get('link', '#')
        
        # Process all entries for their links...
        for curr_entry in feed_data.entries:
            
            # HACK: Ignore entries without modification dates.
            # Maybe improve this by stashing seen dates in a DB.
            if curr_entry.get('modified_parsed', None) is None: 
                continue
            
            # If the current entry is older than the max allowed age,
            # skip processing it.
            now = time.time()
            entry_time = calendar.timegm(curr_entry.modified_parsed)
            if (now - entry_time) > MAX_ENTRY_AGE:
                continue
            
            # Build a LinkSkimmer and feed it all summary and HTML
            # content data from the current entry.  Ignore parse
            # errors in the interest of just grabbing what we can.
            skimmer = LinkSkimmer()
            try:
                skimmer.feed(curr_entry.get('summary',''))
                for c in curr_entry.get('content', []): 
                    skimmer.feed(c.value)
            except HTMLParseError:
                pass
            
            # Process each link by adding the current feed and entry
            # under the link's key in the inverted index.
            for uri, cnt in skimmer.get_links():
                if not links.has_key(uri): 
                    links[uri] = {}
                if not links[uri].has_key(feed_link):
                    links[uri][feed_link] = (feed, curr_entry)
        
    # Turn the inverted index of links into a list of tuples, sort by
    # popularity of links as measured by number of linked entries.
    links_sorted = links.items()
    links_sorted.sort(lambda a,b: cmp(len(b[1].keys()), len(a[1].keys())))
    
    # Build the overall entry content from all the links.
    links_out = []
    for x in links_sorted:
        
        # Get the link and the list of linkers, skip this link if there
        # aren't enough linkers counted.
        link, linkers = x
        if len(linkers) < MIN_LINKS: continue
        
        # Build the list of linkers for this link by populating the
        # LINKER_TMPL string template.
        linkers_out = []
        for feed, entry in linkers.values():
            linkers_out.append(LINKER_TMPL % {
                'feed.title'  : feed.get('title', 'untitled'),
                'feed.link'   : feed.get('link', '#'),
                'entry.title' : entry.get('title', 'untitled'),
                'entry.link'  : entry.get('link', '#'),
            })

        # Build the content block for this link by populating the
        # LINK_TMPL string template.
        links_out.append(LINK_TMPL % {
            'link'       : link,
            'link_cnt'   : len(linkers),
            'linkers'    : '\n'.join(linkers_out)
        })

    # Complete building the content for this entry by populating the
    # CONTENT_TMPL string template.
    out = CONTENT_TMPL % '\n'.join(links_out)
    
    # Construct and append a new entry
    entry = FeedEntryDict({
        'title'   : TITLE_TMPL % {
            'link_cnt' : len(links_out),
            'time'     : time.strftime(TITLE_TIME_FMT)
        },
        'link'    : '',
        'summary' : out
    })
    f.append_entry(entry)
    
    # Output the current feed entries as both RSS and Atom
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())
    
class LinkSkimmer(HTMLParser):
    """
    Quick and dirty link harvester.
    """
    def reset(self):
        """Reset the parser and the list of links."""
        HTMLParser.reset(self)
        self.links = {}
        
    def get_links(self):
        """Return the links found as a list of tuples, link and count."""
        return self.links.items()
        
    def handle_starttag(self, tag, attrs_tup):
        """Harvest href attributes from link tags"""
        attrs = dict(attrs_tup)
        if tag == "a" and attrs.has_key('href'):
            self.links[attrs['href']] = self.links.get(attrs['href'], 0) + 1
    
if __name__=='__main__': main()

