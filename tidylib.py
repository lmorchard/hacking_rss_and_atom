#!/usr/bin/env python
"""
tidylib.py

Utility module/program for running web pages through HTML Tidy.
"""
import sys, popen2
from urllib2 import urlopen

TIDY_CMD  = "/Users/deusx/local/bin/tidy"

TIDY_OPTS = dict(
    output_xhtml=1, force_output=1, numeric_entities=1,
    char_encoding='utf8', indent=1, wrap=0, show_errors=0, 
    show_warnings=0
)

def main():
    """Try to tidy up the source of a URL."""
    print tidy_url(sys.argv[1])

try:
    # Attempt to import utidylib.  If present, use it for 
    # HTML Tidy access.
    from tidy import parseString
    def tidy_string(src):
        return str( tidy.parseString(src, **TIDY_OPTS) )
except:
    # If there was a problem importing utidylib, try using an 
    # external process calling on the command line version. 
    def tidy_string(src):
        opts = " ".join([ "--%s %s" % 
                          (k.replace('_','-'), v) 
                          for k,v in TIDY_OPTS.items() ])
        cmd = "%s %s" % (TIDY_CMD, opts)
        (o, i, e) = popen2.popen3(cmd)
        i.write(src)
        i.flush()
        i.close()
        return o.read()

def tidy_url(url):
    """Given a URL, return a tidied version of its source."""
    src = urlopen(url).read()
    return tidy_string(src)

if __name__=="__main__": main()
