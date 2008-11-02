#!/usr/bin/env python
"""
ch11_pytailgrep.py

Simple, naive implementation of a tail with grep.
"""
import sys, re

def main():
    num_lines = int(sys.argv[1])
    filename  = sys.argv[2]
    pattern   = re.compile(sys.argv[3])

    lines     = open(filename, 'r').readlines()[-num_lines:]
    filtered  = [ x for x in lines if pattern.match(x) ]
                      
    print "".join(filtered)

if __name__ == '__main__': main()
