#!/usr/bin/env python
"""
ch10_bookmark_tailgrep.py

Stateful tail, remembers where it left off reading.
"""
import sys, os, re, shelve

def main():
    """
    Run the bookmark_tailgrep function as a command.
    Usage: ch10_bookmark_tailgrep.py <input file> [<regex>]
    """
    filename = sys.argv[1]

    if len(sys.argv) > 2:
        pattern  = re.compile(sys.argv[2])
        pattern_filter = lambda x: ( pattern.match(x) is not None )
        new_lines = bookmark_tailgrep(filename, pattern_filter)
    else:
        new_lines = bookmark_tailgrep(filename)
    
    sys.stdout.write("".join(new_lines))
    
class BookmarkInvalidException(Exception): pass

def bookmark_tailgrep(tail_fn, line_filter=lambda x: True, 
        state_fn="tail_bookmarks", max_initial_lines=50):
    """
    Stateful file tail reader which keeps a line number bookmark of 
    where it last left off for a given filename.
    """
    fin      = open(tail_fn, 'r')
    state    = shelve.open(state_fn)
    last_num = state.get(tail_fn, 0)
    
    try:
        # Fast foward through file to bookmark.
        for idx in range(last_num):
            # If EOF hit before bookmark, it's become invalid.
            if fin.readline() == '': 
                raise BookmarkInvalidException
    
    except BookmarkInvalidException:
        # In case of invalid bookmark, rewind to start of file.
        last_num = 0
        fin.seek(0)
    
    # Grab the rest of the lines in the file as new.
    new_lines = fin.readlines()
    
    # Advance the bookmark index.
    state[tail_fn] = last_num + len(new_lines)

    # If rewound to beginning of file, limit to the tail-end.
    if last_num == 0:
        new_lines = new_lines[-max_initial_lines:]
    
    # Pass the new lines through the given line filter
    return [ x for x in new_lines if line_filter(x) ]

if __name__ == '__main__': main()
