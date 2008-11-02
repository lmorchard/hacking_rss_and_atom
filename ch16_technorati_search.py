#!/usr/bin/env python
"""
ch16_technorati_search.py

Perform a search on the Technorati API
"""
import sys, urllib, urllib2, xmltramp
from xml.sax import SAXParseException
from httpcache import HTTPCache

def main():
    tmpl  = 'http://api.technorati.com/search?key=%s&limit=5&query=%s'
    key   = open("technorati-key.txt", "r").read().strip()
    query = (len(sys.argv) > 1) and sys.argv[1] or 'test query'
    url   = tmpl % (key, urllib.quote_plus(query))
    data  = HTTPCache(url).content()
    
    # HACK: I get occasional encoding issues with Technorati, so
    # here's an ugly hack that seems to make things work anyway.
    try:
        doc = xmltramp.parse(data)
    except SAXParseException:
        data = data.decode('utf8', 'ignore').encode('utf8')
        doc = xmltramp.parse(data)

    items = [ x for x in doc.document if x._name == 'item' ]
    for i in items:
        print '"%(title)s"\n\t%(permalink)s' % i
    
if __name__=='__main__': main()
