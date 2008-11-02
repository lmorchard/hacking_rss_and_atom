#!/usr/bin/env python
"""
ch12_mailing_list_feed.py

Use MailScraper to produce a feed from mailing list messages
"""
import sys
from mailfeedlib import MailScraper, POP3Client, IMAP4Client

MAIL_CLIENT = POP3Client(
    host   = '127.0.0.1', 
    port   = '110', 
    user   = 'your_account', 
    passwd = 'your_password'
)

def main():
    """
    Given an argument of 'atom' or 'rss' on the command line,
    produce an Atom or RSS feed.
    """
    scraper = FooListScraper(client=MAIL_CLIENT)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rss':
        print scraper.scrape_rss()
    else:
        print scraper.scrape_atom()

class FooListScraper(MailScraper):
    """
    """
    FEED_META = {
        'feed.title'        : 'My Mailing List Feed',
        'feed.link'         : 'http://www.example.com',
        'feed.tagline'      : 'This is a testing sample feed.',
        'feed.author.name'  : 'l.m.orchard',
        'feed.author.email' : 'l.m.orchard@pobox.com',
        'feed.author.url'   : 'http://www.decafbad.com',
    }
    
    STATE_FN    = "mylist_scraper_state"

    def filter_messages(self, msgs):
        """Return filtered list of messages for inclusion in feed."""
        return [ m for m in msgs 
                 if 'Cron ' in m.get('Subject','') ]
    
if __name__=="__main__": main()
