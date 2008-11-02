#!/usr/bin/env python
"""
ch05_plucker_test.py

Take the Plucker Distiller out for a test drive.
"""
import sys, time
import PyPlucker.Spider

HTML_FN       = "http://www.decafbad.com"
PLUCKER_DIR   = "."
PLUCKER_TITLE = "Sample Plucker Document"
PLUCKER_FN    = "plucker-%s" % time.strftime("%Y%m%d-%H%M%S")
PLUCKER_BPP   = 8
PLUCKER_DEPTH = 1

def main():
    """
    Call the PLucker Distiller to output a test document.
    """
    PyPlucker.Spider.realmain(None, argv=[
        sys.argv[0],
        '-P', PLUCKER_DIR,
        '-f', PLUCKER_FN,
        '-H', HTML_FN,
        '-M', PLUCKER_DEPTH,
        '-N', PLUCKER_TITLE,
        '--bpp', PLUCKER_BPP,
        '--title=%s' % PLUCKER_TITLE,
    ])

if __name__ == "__main__": main()

