#!/usr/bin/env python
"""
cvslib.py

Common parts for use in querying CVS repositories.
"""
import sys, os
import time, calendar
from popen2 import popen4
    
CVS_BIN   = '/sw/bin/cvs'

def main():
    PROJECT  = (len(sys.argv) > 1) and sys.argv[1] or 'ipodder'
    CVS_ROOT = ":pserver:anonymous@cvs.sourceforge.net:/cvsroot/%s" % PROJECT

    client = CVSClient(CVS_ROOT, cvs_bin=CVS_BIN)
    
    events = client.history()
    print '\n'.join(['%(event)s %(revision)s %(path)s' % x 
            for x in events[:5]])
    print
    print client.rlog('1.54', 'site/htdocs/index.php').description

class CVSClient:
    """
    Interface around bits of CVS functionality.
    """

    def __init__(self, root, cvs_bin='/usr/bin/cvs'):
        """
        Initialize the client object with a CVS root and 
        executable path.
        """
        self.root    = root
        self.cvs_bin = cvs_bin

    def _cvs(self, rest):
        """
        Execute a given CVS command, return lines output as a result.
        """
        cmd = "%s -z3 -d%s %s" % (self.cvs_bin, self.root, rest)
        (sout, sin) = popen4(cmd)
        return sout.readlines()
        
    def rlog(self, revision, path):
        """
        Query CVS repository log entries for given revision and path.
        """
        cmd = "rlog -r%s %s" % (revision, path)
        return CVSLogEntry(self._cvs(cmd))

    DEFAULT_HISTORY_TIME = (7 * 24 * 60 * 60) # 1 week
    
    def history(self, since=None, event_types="MAR"):
        """
        Query CVS repository for a list of recent events, defaults to
        last week of commit events.
        """
        # If no time for since given, calculate a default.
        if since is None:
            since = time.time() - self.DEFAULT_HISTORY_TIME

        # Build & execute the CVS history command, wrapping each line of
        # the results with history event objects.  Return the sorted list.
        cmd = "history -x%s -a -z +0000 -D'%s'" % \
            (event_types, time.strftime('%Y-%m-%d', time.localtime(since)))
        try:
            events = [CVSHistoryEvent(x) for x in self._cvs(cmd)]
            events.sort()
            return events
        except:
            # Most common exception stems from no history events available
            # for time range.  Should try to account for others though.
            return []

class CVSLogEntry:
    """
    Encapsulate a parsed CVS log entry.
    """
    def __init__(self, lines):
        """Parse CVS log entry and initialize the object"""
        self.full_entry  = ''.join(lines)
        self.description = ''
        
        # Parse through the lines of the log entry, capturing just the
        # description for now.
        in_description = False
        for line in lines:
            if line.startswith('-----'): in_description = True
            elif line.startswith('====='): in_description = False
            elif in_description:
                self.description = '%s%s' % (self.description, line)
        
    def __getitem__(self, name):
        """Facilitate dictionary-style access to attributes."""
        return getattr(self, name)

class CVSHistoryEvent:
    """
    Encapsulate a parsed CVS history event line.
    """    
    HISTORY_EVENTS = {
        "O" : "Checkout" ,
        "F" : "Release" ,
        "T" : "RTag",
        "W" : "Delete on update",
        "U" : "Update",
        "P" : "Update by patch",
        "G" : "Merge on update",
        "C" : "Conflict on update",
        "M" : "Commit",
        "A" : "Addition",
        "R" : "Removal",
        "E" : "Export",
    }    
    
    def __init__(self, line):
        """Parse the CVS event line into object attributes"""
        (evt, tm, dt, tz, usr, rev, fn, dn) = line.split()[:8]
        
        tm_tup = time.strptime("%s %s" % (tm, dt), "%Y-%m-%d %H:%M")

        self.path        = '%s/%s' % (dn, fn)
        self.user        = usr
        self.revision    = rev
        self.event       = evt
        self.event_label = self.HISTORY_EVENTS.get(evt, evt)
        self.time_tup    = tm_tup
        self.time        = calendar.timegm(tm_tup)

    def __cmp__(self, other):
        """Facilitate reverse-chron order in lists."""
        return cmp(other.time, self.time)

    def __getitem__(self, name):
        """Facilitate dictionary-style access to attributes."""
        return getattr(self, name)
    
if __name__ == '__main__': main()
