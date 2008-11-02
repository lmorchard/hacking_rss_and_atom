#!/usr/bin/env python
"""
ch15_bayes_mark_entry.cgi

Train a Bayes classifier to like or dislike a chosen feed entry.
"""
import sys; sys.path.append('lib')
import cgi, os, logging
import cgitb; cgitb.enable()

from ch15_bayes_agg import ScoredEntryWrapper, findEntry
from ch15_bayes_agg import guessEntry, scoreEntry, trainEntry
from reverend.thomas import Bayes

BAYES_DATA_FN = "bayesdata.dat"

def main():
    """
    Handle training the aggregator from a CGI interface.
    """
    # Load up and parse the incoming CGI parameters.
    form     = cgi.FieldStorage()
    feed_uri = form.getvalue('feed')
    entry_id = form.getvalue('entry')
    like     = ( form.getvalue('like')=='1' ) and 'like' or 'dislike'

    # Create a new Bayes guesser, attempt to load data
    guesser = Bayes()
    guesser.load(BAYES_DATA_FN)

    # Use the aggregator to find the given entry.
    entry = findEntry(feed_uri, entry_id)

    # Print out the content header right away.
    print "Content-Type: text/html"
    print
    
    # Check if a feed and entry were found...
    if entry:
        
        # Take a sample guess before training on this entry.
        before_guess = guessEntry(guesser, entry)
        before_score = scoreEntry(guesser, entry)

        # Train with this entry and classification, save the data.
        trainEntry(guesser, like, entry)
        
        # Take a sample guess after training.
        after_guess = guessEntry(guesser, entry)
        after_score = scoreEntry(guesser, entry)

        # Save the guesser data
        guesser.save(BAYES_DATA_FN)
        
        # Report the results.
        print """
        <html>
            <head><title>Feed entry feedback processed</title></head>
            <body>
                <p>
                    Successfully noted '%(like)s' classification
                    for [%(feed.title)s] %(entry.title)s
                </p>
                <p style="font-size: 0.75em">
                    Before: %(before_score)s %(before_guess)s
                </p>
                <p style="font-size: 0.75em">
                    After: %(after_score)s %(after_guess)s
                </p>
            </body>
        </html>
        """ % {
            'like'         : like,
            'feed.title'   : entry['feed.title'],
            'entry.title'  : entry['entry.title'],
            'feed.uri'     : entry['feed.uri'],
            'entry.id'     : entry['id'],
            'before_guess' : before_guess,
            'before_score' : before_score,
            'after_score'  : after_score,
            'after_guess'  : after_guess
        }

    else:
        # Couldn't find a corresponding entry, report the bad news.
        print """
        <html>
            <body>
                <p>
                    Sorry, couldn't find a matching entry for this
                    feed URI and entry ID:
                </p>
                <ul>
                    <li>Feed: %(feed.uri)s</li>
                    <li>Entry: %(entry.id)s</li>
                </ul>
            </body>
        </html>
        """ % {
            'feed.uri'     : feed_uri,
            'entry.id'     : entry_id,
        }

if __name__=='__main__': main()
