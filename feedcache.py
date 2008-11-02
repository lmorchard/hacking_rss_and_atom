#!/usr/bin/env python
"""
feedcache

Implements a shared cache of feed data polled via feedparser.
"""
import sys, os, os.path, md5, gzip, feedparser, time
import cPickle as pickle

def main():
    """
    Either print out a parsed feed, or refresh all feeds.
    """
    feed_cache = FeedCache()
    if len(sys.argv) > 1:
        # In demonstration, fetch and pretty-print a parsed feed.
        from pprint import pprint
        pprint(feed_cache.parse(sys.argv[1]))
    else:
        # Open up the feed cache and refresh all the feeds
        feed_cache.refreshFeeds() 

class FeedCacheRecord:
    """
    Record stored in feed cache.
    """
    def __init__(self, last_poll=0.0, etag='', modified=None, data=None):
        """Initialize the cache record."""
        self.last_poll = last_poll
        self.etag      = etag
        self.modified  = modified
        self.data      = data

class FeedCache:
    """
    Implements a cache of refreshed feed data.
    """
    CACHE_DIR      = ".feed_cache"
    REFRESH_PERIOD = 60 * 60
    
    def __init__(self, cache_dir=CACHE_DIR, refresh_period=REFRESH_PERIOD):
        """
        Initialize and open the cache.
        """
        self.refresh_period = refresh_period
        self.cache_dir      = cache_dir

        # Create the cache dir, if it doesn't yet exist.
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
    def parse(self, feed_uri, **kw):
        """
        Partial feedparser API emulation, only accepts a URI.
        """
        self.refreshFeed(feed_uri)
        return self.getFeedRecord(feed_uri).data
        
    def getFeedRecord(self, feed_uri):
        """
        Fetch a feed cache record by URI.
        """
        return self._loadRecord(feed_uri, None)

    def refreshFeeds(self):
        """
        Refresh all the feeds in the cache.
        """
        # Load up the list of feed URIs, report how many feeds 
        # in cache and start processing.
        feed_uris  = self._getCachedURIs()
        for feed_uri in feed_uris:
            try:
                # Refresh the current feed URI
                self.refreshFeed(feed_uri)
            except KeyboardInterrupt:
                # Allow keyboard interrupts to stop the program.
                raise
            except Exception, e:
                # Soldier on through any other problems.
                pass
    
    def refreshFeed(self, feed_uri):
        """
        Refresh a given feed.
        """
        # Get the record for this feed, creating a new one if necessary.
        feed_rec = self._loadRecord(feed_uri, FeedCacheRecord())
        
        # Check to see whether it's time to refresh this feed yet.
        # TODO: Respect/obey TTL, update schedule, cache control headers.
        if (time.time() - feed_rec.last_poll) < self.refresh_period:
            pass
        else:
            # Fetch the feed using the ETag and Last-Modified notes.
            feed_data = feedparser.parse(feed_uri,\
                etag=feed_rec.etag, modified=feed_rec.modified)
            feed_rec.last_poll = time.time()
            
            bozo = feed_data.get('bozo_exception', None) 
            if bozo is not None:
                # Throw any keyboard interrupts that happen in parsing.
                if type(bozo) is KeyboardInterrupt: raise bozo
                    
                # Don't try to shelve exceptions, it's bad.
                # (TODO: Maybe save this in a text form, for troubleshooting.)
                del feed_data['bozo_exception']
    
            # If the feed HTTP status is 304, there was no change.
            if feed_data.get('status', -1) != 304:
                feed_rec.etag     = feed_data.get('etag', '')
                feed_rec.modified = feed_data.get('modified', None)
                feed_rec.data     = feed_data

            # Update the feed cache record.
            self._saveRecord(feed_uri, feed_rec)
    
    # Watch for subclassable parts below here.
    
    def _recordFN(self, feed_uri):
        """
        Return the filename for a given feed URI.
        """
        hash = md5.md5(feed_uri).hexdigest()
        return os.path.join(self.cache_dir, '%s' % hash)

    def _getCachedURIs(self):
        """
        Get a list of feed URIs in the cache.
        """
        uris = []
        for fn in os.listdir(self.cache_dir):
            rec_fn = os.path.join(self.cache_dir, fn)
            data   = pickle.load(open(rec_fn, 'rb'))
            uri    = data['data'].get('url', None)
            if uri: uris.append(uri)
        return uris
    
    def _loadRecord(self, feed_uri, default=None):
        """
        Load a FeedCacheRecord from disk.
        """
        try:
            rec_fn = self._recordFN(feed_uri)
            data   = pickle.load(open(rec_fn, 'rb'))
            return FeedCacheRecord(**data)
        except IOError:
            return default

    def _saveRecord(self, feed_uri, record):
        """
        Save a FeedCacheRecord to disk.
        """
        rec_fn = self._recordFN(feed_uri)
        pickle.dump(record.__dict__, open(rec_fn, 'wb'))

def parse(feed_uri, cache=None, **kw):
    """
    Partial feedparser API emulation, only accepts a URI.
    """
    return (cache or FeedCache()).parse(feed_uri, **kw)

if __name__=='__main__': main()
