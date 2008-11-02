#!/usr/bin/env python
"""
ch10_logins_feed.py

Provide reports of login activity.
"""
import sys, os, difflib, gzip
from xml.sax.saxutils import escape
from popen2 import popen4
from scraperlib import FeedEntryDict
from monitorfeedlib import LogBufferFeed

SITE_NAME    = "0xDECAFBAD"
COMMAND      = "/usr/bin/last -a"
FEED_NAME_FN = "www/www.decafbad.com/docs/private-feeds/logins.%s"
FEED_DIR     = "logins_feed"

TITLE_TMPL   = "Command output update (%(changes)s changes)"
SUMMARY_TMPL = """
    <p>Changes:</p>
    <div style="font-family: monospace">%(changes_lines)s</div>

    <p>All lines:</p>
    <div style="font-family: monospace">%(diff_lines)s</div>
"""

def main():
    """
    Detect login activity changes and report in feed.
    """
    # Construct the feed generator
    f = LogBufferFeed(FEED_DIR)
    f.MAX_AGE = 24 * 60 * 60 # 1 day
    f.FEED_META['feed.title']   = '%s Login Activity' % SITE_NAME
    f.FEED_META['feed.tagline'] = \
        'Summary of login activity on the %s server' % SITE_NAME
   
    # Call the command and capture output
    (sout, sin) = popen4(COMMAND) 
    new_lines   = [ x for x in sout.readlines() 
                    if x.find('reboot') == -1 ]
    
    # Attempt load up output from the previous run.
    old_lines = None
    old_output_fn = os.path.join(FEED_DIR, 'old_output.gz')
    if os.path.exists(old_output_fn):
        old_lines = gzip.open(old_output_fn, "r").readlines()
    
    # If there is previous output, check for changes...
    if old_lines:
        
        # Run a diff on the previous and current program output.
        diff_lines = [ x for x in difflib.ndiff(old_lines, new_lines) ]

        # Extract only the lines that have changed.
        changes_lines = [ x for x in diff_lines 
                          if x.startswith('-') or x.startswith('+') ]
        
        # Construct and append a new entry if there were changes
        if len(changes_lines) > 0:
            esc_changes_lines = [escape(x) for x in changes_lines]
            esc_diff_lines = [escape(x) for x in diff_lines]
            entry = FeedEntryDict({
                'link'    : '',
                'title'   : TITLE_TMPL % { 
                    'changes' : len(changes_lines) 
                },
                'summary' : SUMMARY_TMPL % {
                    'changes_lines' : "<br />".join(esc_changes_lines),
                    'diff_lines'    : "<br />".join(esc_diff_lines)
                }
            })
            f.append_entry(entry)

    # Save output from the current run for use next time.
    gzip.open(old_output_fn, "w").write("".join(new_lines))

    # Output the current feed entries as both RSS and Atom
    open(FEED_NAME_FN % 'rss', 'w').write(f.scrape_rss())
    open(FEED_NAME_FN % 'atom', 'w').write(f.scrape_atom())

if __name__ == '__main__': main()
