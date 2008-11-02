#!/usr/bin/env python
"""
ch17_feed_to_javascript.py

Fetch and parse a feed, render it as JavaScript code suitable 
for page include.
"""
import sys, feedparser
from httpcache import HTTPCache
from ch14_feed_normalizer import normalize_entries

FEED_URL = "http://www.decafbad.com/blog/index.xml"
JS_FN    = "feed-include.js"

def main():
    """
    Accepts optional arguments including feed url and JavaScript
    code filename.
    """
    feed_url = ( len(sys.argv) > 1 ) and sys.argv[1] or FEED_URL
    js_fn    = ( len(sys.argv) > 2 ) and sys.argv[2] or JS_FN
    js_feed  = JavaScriptFeed(feed_url)
    out      = js_feed.build()
    open(js_fn, "w").write(out)

class JavaScriptFeed:
    """
    Class which facilitates the formatting of a feed as a JavaScript
    page include.
    """
    
    UNICODE_ENC = 'UTF-8'
    
    INCLUDE_TMPL = """
        <b>%(feed.title)s included via JavaScript:</b>
        <ul>
            %(feed.entries)s
        </ul>
    """

    ENTRY_TMPL = """
        <li>
            <b><a href="%(link)s">%(title)s</a></b>:
            <blockquote>
                %(summary)s
            </blockquote>
        </li>
    """

    def __init__(self, feed_url):
        self.feed_url = feed_url

    def build(self):
        """
        Fetch feed data and return JavaScript code usable as an include
        to format the feed as HTML.
        """
        # Fetch and parse the feed
        cache     = HTTPCache(self.feed_url) 
        feed_data = feedparser.parse(cache.content())

        # Build a list of content strings by populating entry template
        entries_out = [ self.ENTRY_TMPL % {
            'link'    : entry.get('link',  ''),
            'title'   : entry.get('title', ''),
            'summary' : entry.get('summary', ''),
        } for entry in feed_data.entries ]

        # Build final content by populating the overall shell template
        out = self.INCLUDE_TMPL % {
            'feed.title'   : feed_data.feed.title,
            'feed.entries' : "\n".join(entries_out)
        }

        # Encode the content using the object unicode encoding
        out = out.encode(self.UNICODE_ENC)
        
        # Return the content wrapped in JavaScript code
        return self.js_format(out)

    def js_format(self, out):
        """Wrap a string of content in JavaScript code for include"""
        lines_out = []
        for line in out.splitlines():
            line = line.replace('\\', '\\\\')
            line = line.replace('"', '\\"')
            line = 'document.writeln("%s");' % line
            lines_out.append(line)
        
        return "\n".join(lines_out)

if __name__ == "__main__": main()
