#!/usr/bin/env python
"""
ch14_xslt_normalizer.py

Use 4Suite to apply an XSLT to a URL
"""
import sys
from Ft.Xml.Xslt import Processor
from Ft.Xml.InputSource import DefaultFactory

FEED_URL = 'http://www.decafbad.com/blog/index.xml'

def main():
    """
    """
    feed_format = ( len(sys.argv) > 1 ) and sys.argv[1] or 'atom'
    feed_url    = ( len(sys.argv) > 2 ) and sys.argv[2] or FEED_URL
    
    source    = DefaultFactory.fromUri(feed_url)
    
    trans_fin = open('ch14_xslt_normalizer.xsl', 'r')
    trans_url = 'http://www.decafbad.com/2005/04/ch14_xslt_normalizer.xsl'
    transform = DefaultFactory.fromStream(trans_fin, trans_url)
    
    processor = Processor.Processor()
    processor.appendStylesheet(transform)
    
    result = processor.run(source, 
                           topLevelParams={'format':feed_format})
    print result

if __name__=='__main__': main()

