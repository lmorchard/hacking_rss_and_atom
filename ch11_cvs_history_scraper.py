#!/usr/bin/env python
"""
ch11_cvs_history_scraper.py

Build a feed from recent commit history queries 
from a remote CVS repository.
"""
import sys
from urllib import quote
from cvslib import CVSClient
from scraperlib import Scraper, FeedEntryDict

CVS_BIN   = '/sw/bin/cvs'

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    project = (len(sys.argv) > 2) and sys.argv[2] or 'ipodder'
    
    cvs_root = \
        ":pserver:anonymous@cvs.sourceforge.net:/cvsroot/%s" % project
    cvs_client = CVSClient(cvs_root, cvs_bin=CVS_BIN)
    
    scraper = CVSScraper(cvs_client)

    scraper.LINK_TMPL = \
        "http://cvs.sourceforge.net/viewcvs.py/%s/" % project + \
        "%(path)s?rev=%(revision)s&view=auto"
   
    scraper.TAG_PREFIX = 'decafbad.com,2005-03-20:%s' % project
    
    scraper.FEED_META['feed.title'] = \
        "SourceForge CVS changes for '%s'" % project
    scraper.FEED_META['feed.link']     = \
        "http://%s.sourceforge.net" % project
    scraper.FEED_META['feed.tagline']  = ""    
     
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class CVSScraper(Scraper):
    """
    Using a CVSClient object, scrape a feed from recent history events.
    """
    TAG_PREFIX  = 'decafbad.com,2005-03-20:cvs_scraper'
    STATE_FN    = 'cvs_scraper_state'
    TITLE_TMPL  = "%(event_label)s (r%(revision)s) by %(user)s: %(path)s"
    LINK_TMPL   = ""

    def __init__(self, client):
        """Initialize with the given CVS client."""
        self.client = client

    def produce_entries(self):
        """
        Build feed entries based on queried CVS history events.
        """
        events  = self.client.history()
        
        entries = []
        for event in events[:self.MAX_ENTRIES]:
            # Build a GUID for this entry
            cvs_id   = '%(path)s:%(revision)s' % event
            entry_id = 'tag:%s%s' % (self.TAG_PREFIX, quote(cvs_id))
            
            # Attempt to grab an existing state record for this entry ID.
            if not self.state_db.has_key(entry_id): 
                self.state_db[entry_id] = {}
            entry_state = self.state_db[entry_id]
            
            # If this entry's state doesn't already have a description
            # cached, query CVS for the log entry and grab the it.
            if not entry_state.has_key('description'):
                log_entry = self.client.rlog(event.revision, event.path)
                entry_state['description'] = log_entry.description
            description = entry_state['description']

            # Build the feed entry based on the CVS event and log entry
            entry = FeedEntryDict(init_dict={
                'id'          : entry_id,
                'title'       : self.TITLE_TMPL % event,
                'link'        : self.LINK_TMPL % event,
                'author.name' : event.user,
                'modified'    : event.time,
                'issued'      : event.time,
                'summary'     : '<pre>%s</pre>' % description
            }, date_fmt=self.date_fmt)
            
            # Append the completed entry to the list, and save the 
            # entry state.
            entries.append(entry)
            self.state_db[entry_id] = entry_state

        return entries

if __name__ == '__main__': main()

