#!/usr/bin/env python
"""
ch07_feedmaker.py

Create an RSS feed from a collection of HTML documents
"""
import sys, time, urlparse, urllib, htmlmetalib
from xml.sax.saxutils import escape

BASE_HREF   = 'http://www.example.com'
TAG_DOMAIN  = 'example.com'
MAX_ENTRIES = 15

FEED_META = {
    'feed.title'        : 'A Sample Feed',
    'feed.link'         : 'http://www.example.com',
    'feed.tagline'      : 'This is a testing sample feed.',
    'feed.author.name'  : 'l.m.orchard',
    'feed.author.email' : 'l.m.orchard@pobox.com',
    'feed.author.url'   : 'http://www.decafbad.com'
}

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
        <issued>%(entry.modified)s</issued>
        <modified>%(entry.modified)s</modified>
        <id>%(entry.id)s</id>
        <summary type="text/html" mode="escaped">
            %(entry.content)s
        </summary>
    </entry>
"""

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

def main():
    """
    Find all HTML documents in a given path and produce a 
    syndication feed based on the pages' metadata.
    """
    #FEED_TMPL   = RSS_FEED_TMPL
    #ENTRY_TMPL  = RSS_ENTRY_TMPL
    #doc_wrapper = RSSTemplateDocWrapper
    
    FEED_TMPL   = ATOM_FEED_TMPL
    ENTRY_TMPL  = ATOM_ENTRY_TMPL
    doc_wrapper = AtomTemplateDocWrapper
    
    # Find all the HTML docs.
    docs = htmlmetalib.findHTML(sys.argv[1])
    
    # Bundle all the HTML doc objects in template-friendly wrappers.
    entries = [ doc_wrapper(BASE_HREF, TAG_DOMAIN, d) for d in docs ]
    entries.sort()
    
    # Build a map for the feed template.
    data_out = {}
    data_out.update(FEED_META)
    entries_out = [ENTRY_TMPL % e for e in entries[:MAX_ENTRIES]]
    data_out['feed.modified'] = \
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data_out['feed.entries'] = "".join(entries_out)

    # Handle optional parameter to output to a file
    if len(sys.argv) > 2:
        fout = open(sys.argv[2], "w")
    else:
        fout = sys.stdout
    
    # Fill out the feed template and output.
    fout.write(FEED_TMPL % data_out)

class TemplateDocWrapper:
    """
    This class is a wrapper around HTMLMetaDoc objects meant to 
    facilitate easy use in XML template strings.
    """
    UNICODE_ENC  = "UTF-8"
    MODIFIED_FMT = "%Y-%m-%dT%H:%M:%SZ"
    
    def __init__(self, base_href, tag_domain, doc):
        """Initialize the wrapper"""
        self._base_href  = base_href
        self._tag_domain = tag_domain
        self._doc        = doc
       
    def __cmp__(self, other):
        """Use the docs' comparison method."""
        return cmp(self._doc, other._doc)

    def __getitem__(self, name):
        """
        Translate map-like access from a template into proper values
        based on document attributes.
        """
        if name == "entry.title": 
            # Return the document's title.
            val = self._doc.title
        
        elif name == "entry.summary": 
            # Return the document's description
            val = self._doc.description
            
        elif name == "entry.content": 
            # Return the document's content
            val = self._doc.content

        elif name == "entry.link":
            # Construct entry's link from document path and base HREF
            val = urlparse.urljoin(self._base_href, self._doc.path)
        
        elif name == "entry.modified":
            # Use the class modified time format to create the string
            val = time.strftime(self.MODIFIED_FMT,
                    time.gmtime(self._doc.modified))
            
        elif name == "entry.id":
            # Construct a canonical tag URI for the entry GUID
            ymd = time.strftime("%Y-%m-%d", 
                    time.gmtime(self._doc.modified))
            val = "tag:%s,%s:%s" % (self._tag_domain, ymd, 
                    urllib.quote(self._doc.path,''))
        
        else:
            # Who knows what the template wanted?
            val = "(undefined)"
        
        # Make sure the value is finally safe for inclusion in XML
        return escape(val.encode(self.UNICODE_ENC))

class AtomTemplateDocWrapper(TemplateDocWrapper):
    """Template wrapper for Atom-style entries"""
    MODIFIED_FMT = "%Y-%m-%dT%H:%M:%SZ"
    
class RSSTemplateDocWrapper(TemplateDocWrapper):
    """Template wrapper for RSS-style entries"""
    MODIFIED_FMT = "%a, %d %b %Y %H:%M:%S %z"

if __name__ == "__main__": main()
