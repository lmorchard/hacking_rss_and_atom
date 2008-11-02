#!/usr/bin/env python
"""
ch10_apache_referrer_feed.py

Scan the Apache access log for new referring links, build 
mini-reports in feed entries.
"""
import sys, os, re, shelve
from scraperlib import FeedEntryDict
from monitorfeedlib import LogBufferFeed
from ch10_bookmark_tailgrep import bookmark_tailgrep

SITE_NAME    = "0xDECAFBAD"
SITE_ROOT    = "http://www.decafbad.com"
ACCESS_LOG   = "www/www.decafbad.com/logs/access.log" 
FEED_NAME_FN = "www/www.decafbad.com/docs/private-feeds/referrers.%s"
FEED_DIR     = "referrer_feed"
REFER_SEEN   = "%s/referrer_seen" % FEED_DIR

EXCLUDE_EXACT = {
    'referrer' : [ '', '-' ],
    'path'     : [ '/', 'http://www.decafbad.com' ]
}

EXCLUDE_PARTIAL = {
    'referrer' : [ 'decafbad.com', 'porn', 'xxx', 'hardcore', 'incest', 
                   'gay', 'sex', 'terra', 'viagra', 'poker', 'casino',
                   'holdem', 'google.com', 'slots', 'roulette', 'vinhas', 
                   'gaming.win', 'baccarat', 'betting', 'black-jack',
                   'scat', 'dmozx', 'old-young', 'rape', 'conjuratia',
                   'bloglines', 'google' ],
    'path'     : [ '/images/', '.rss', '.rdf', '.xml' ]
}

SUMMARY_TMPL = """
    <p>Found %(count)s new referring links:</p>
    %(links)s
"""

LINK_TMPL = """
    <table style="margin: 2px; padding: 2px; border: 1px solid #888">
        <tr style="background: #fff">
            <th>From:</th>
            <td><a href="%(referrer)s">%(referrer)s</a></td>
        </tr>
        <tr style="background: #eee">
            <th>To:</th>
            <td><a href="%(SITE_ROOT)s%(path)s">%(path)s</a></td>
        </tr>
    </table>
"""

def main():
    """
    Scan Apache log and report new referrers found.
    """
    # Construct the feed generator
    f = LogBufferFeed(FEED_DIR)
    f.MAX_AGE = 24 * 60 * 60 # 1 day
    f.FEED_META['feed.title']   = '%s Referrering Links' % SITE_NAME
    f.FEED_META['feed.tagline'] = \
        'New referring links from Apache access.log on %s' % SITE_NAME
    
    # Load up tail of access log, parse, and filter
    new_lines  = bookmark_tailgrep(ACCESS_LOG, max_initial_lines=100000)
    all_events = parse_access_log(new_lines)
    events     = [ x for x in all_events if event_filter(x) ]
    
    # Scan through latest events for new referrers
    referrers_seen = shelve.open(REFER_SEEN)
    new_referrers  = []
    for evt in events:
        k = '%(referrer)s -> %(path)s' % evt
        if not referrers_seen.has_key(k):
            referrers_seen[k] = 1
            new_referrers.append( (evt['referrer'], evt['path']) )
    referrers_seen.close()
    
    # If there were new referrers found, insert a new entry.
    if len(new_referrers) > 0:
        
        # Build a list of hyperlinks for referrers
        links_out = [
            LINK_TMPL % {
                'SITE_ROOT' : SITE_ROOT,
                'referrer'  : x[0],
                'path'      : x[1],
            }
            for x in new_referrers
        ]
        
        # Build a summary for this entry.
        summary = SUMMARY_TMPL % { 
            'count' : len(new_referrers), 
            'links' : "\n".join(links_out)
        }
        
        # Construct and append a new entry
        entry = FeedEntryDict({
            'title'   : '%s new referrers' % len(new_referrers),
            'link'    : '',
            'summary' : summary
        })
        f.append_entry(entry)

    # Output the current feed entries as both RSS and Atom
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())

def event_filter(event):
    """Filter events on exact and partial exclusion criteria"""
    for field, blst in EXCLUDE_PARTIAL.items():
        ev_val = event[field]
        for bl_val in blst:
            if ev_val.find(bl_val) != -1: return False
    
    for field, blst in EXCLUDE_EXACT.items():
        ev_val = event[field]
        for bl_val in blst:
            if ev_val == bl_val: return False
    
    return True

ACCESS_RE = re.compile(\
    '(?P<client_ip>\d+\.\d+\.\d+\.\d+) '
    '(?P<ident>-|\w*) '
    '(?P<user>-|\w*) '
    '\[(?P<date>[^\[\]:]+):'
    '(?P<time>\d+:\d+:\d+) '
    '(?P<tz>.\d\d\d\d)\] '
    '"(?P<method>[^ ]+) '
    '(?P<path>[^ ]+) '
    '(?P<proto>[^"]+)" '
    '(?P<status>\d+) (?P<length>-|\d+) '
    '"(?P<referrer>[^"]*)" '
    '(?P<user_agent>".*")\s*\Z'
)

def parse_access_log(log_lines):
    """Parse Apache log file lines via regex"""
    matches = [ ACCESS_RE.search(y) for y in log_lines ]
    return [ x.groupdict() for x in matches if x is not None ]

if __name__ == '__main__': main()
