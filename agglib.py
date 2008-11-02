#!/usr/bin/env python
"""
agglib

A reusable module library of things useful for feed aggregator.
"""
import sys, time, feedparser, feedfinder, shelve, md5, time

UNICODE_ENC = "utf-8"

def openDBs(feed_db_fn, entry_db_fn):
    """
    Open the databases used to track feeds and entries seen.
    """
    feed_db  = shelve.open(feed_db_fn)
    entry_db = shelve.open(entry_db_fn)
    return (feed_db, entry_db)

def closeDBs(feed_db, entry_db):
    """
    Close the databases used to track feeds and entries seen.
    """
    feed_db.close()
    entry_db.close()

def getNewFeedEntries(feeds, feed_db, entry_db):
    """
    Given a list of feeds, poll feeds which have not been polled in over
    an hour.  Look out for conditional HTTP GET status codes before 
    processing feed data.  Check if we've seen each entry in a feed,
    collecting any entries that are new.  Sort the entries, then return 
    the list.
    """
    entries = []
    for uri in feeds:
        print "Polling %s" % uri
        try:
            # Get the notes rememebered for this feed.
            feed_data = feed_db.get(uri, {})
            last_poll = feed_data.get('last_poll', None)
            etag      = feed_data.get('etag', None)
            modified  = feed_data.get('modified', None)
            
            # Check to see whether it's time to poll this feed yet.
            if last_poll and (time.time() - last_poll) < 3600:
                print "\tFeed already polled within the last hour."
            
            else:
                # Fetch the feed using the ETag and Last-Modified notes.
                feed_data = feedparser.parse(uri,etag=etag,modified=modified)
                
                # If the feed HTTP status is 304, there was no change.
                if feed_data.status == 304:
                    print "\tFeed unchanged."
                
                else:
                    new_entries = 0
                    
                    for entry_data in feed_data.entries:
                    
                        # Wrap the entry data and get a hash for the entry.
                        entry = EntryWrapper(feed_data, entry_data)
                        hash  = entry.hash()
                        
                        # If the hash for this entry is found in the DB, 
                        # it's not new.
                        if entry_db.has_key(hash): continue

                        # Flag entry as seen with the hash key, append to 
                        # list of new entries.
                        entry_db[hash] = time.time()
                        entries.append(entry)
                        new_entries += 1
                    
                    print "\tFound %s new entries" % new_entries

            # Finally, update the notes remembered for this feed.
            if feed_data.has_key('feed') and feed_data['feed'].has_key('title'):
                feed_title = feed_data['feed']['title']
            else:
                feed_title = 'Untitled'

            feed_db[uri] = {
                'last_poll' : time.time(),
                'etag'      : feed_data.get('etag', None),
                'modified'  : feed_data.get('modified', None),
                'title'     : feed_title
            }
            
        except KeyboardInterrupt:
            raise
        except Exception, e:
            print "Problem polling %s: %s" % (uri, e)
    
    entries.sort()
    return entries

def writeAggregatorPage(entries, out_fn, date_hdr_tmpl, feed_hdr_tmpl, 
        entry_tmpl, page_tmpl):
    """
    Given a list of entries and an output filename, use templates to compose
    an aggregate page from the feeds and write to the file.
    """
    out, curr_day, curr_feed = [], None, None

    for e in entries:
        # If this entry's date is not the current running day, change the 
        # current day and add a date header to the page output.
        if e['date'] != curr_day:
            curr_day = e['date']
            out.append(date_hdr_tmpl % curr_day)
            
            # Oh yeah, and output a reminder of the current feed after the
            # day header if it hasn't changed.
            if e.feed.title == curr_feed:
                out.append(feed_hdr_tmpl % e)
        
        # If this entry's feed isn't the current running feed, change the
        # current feed and add a feed header to the page output.
        if e.feed.title != curr_feed:
            curr_feed = e.feed.title
            out.append(feed_hdr_tmpl % e)
        
        # Add the entry to the page output.
        out.append(entry_tmpl % e)

    # Concatenate all the page output collected, fill the page templage, and
    # write the result to the output file.
    open(out_fn, "w").write(page_tmpl % "".join(out))

def sendEntriesViaIM(conn, to_nick, entries, im_chunk, feed_hdr_tmpl,
        entry_tmpl, msg_tmpl):
    """
    Given an IM connection, a destination name, and a list of entries,
    send off a series of IMs containing entries rendered via template.
    """
    out, curr_feed, entry_cnt = [], None, 0
    for entry in entries:

        # If there's a change in current feed, note it and append a 
        # feed header onto the message.
        if entry.feed.title != curr_feed:
            curr_feed = entry.feed.title
            out.append(feed_hdr_tmpl % entry)

        # Append the current entry to the outgoing message
        out.append(entry_tmpl % entry)

        # Keep count of entries.  Every IM_CHUNK worth, fire off the
        # accumulated message content as an IM and clear the current 
        # feed title to force a new header in the next batch.
        entry_cnt += 1
        if (entry_cnt % im_chunk) == 0:
            sendIMwithTemplate(conn, to_nick, out, msg_tmpl)
            out, curr_feed = [], None

    # Flush out any remaining content.
    if len(out) > 0:
        sendIMwithTemplate(conn, to_nick, out, msg_tmpl)

def sendIMwithTemplate(conn, to_nick, out, msg_tmpl):
    """
    Given an IM bot, a destination name, and a list of content, render
    the message template and send off the IM.
    """
    try:
        msg_text = msg_tmpl % "".join(out)
        conn.sendIM(to_nick, msg_text)
        time.sleep(4)
    except KeyboardInterrupt:
        raise
    except Exception, e:
        print "\tProblem sending IM: %s" % e

def loadSubs(feeds_fn):
    """
    Load up a list of feeds.
    """
    return [ x.strip() for x in open(feeds_fn, "r").readlines() ]

def saveSubs(feeds_fn, feeds):
    """
    Save a list of feeds.
    """
    open(feeds_fn, "w").write("\n".join(feeds))

class SubsException(Exception):
    def __init__(self, uri=None):
        Exception.__init__(self)
        self._uri = uri
        
class SubsNotSubscribed(SubsException): 
    pass

def unsubscribeFeed(feeds, uri):
    """
    Attempt to remove a URI from the give list of subscriptions.
    Throws a SubsNotSubscribed exception if the URI wasn't found in the
    subscriptions.
    """
    if uri not in feeds: raise SubsNotSubscribed(uri)
    feeds.remove(uri)
    
class SubsAlreadySubscribed(SubsException):
    pass

class SubsNoFeedsFound(SubsException): 
    pass

class SubsMultipleFeedsFound(SubsException):
    def __init__(self, uri=None, feeds=[]):
        SubsException.__init__(self, uri)
        self._feeds = feeds
    def getFeeds(self):
        return self._feeds

def subscribeFeed(feeds, uri):
    """
    Given a list of feeds and a URI at which to find feeds, try
    adding this feeds to the list.
    """
    feeds_found = feedfinder.getFeeds(uri)

    if len(feeds_found) == 0:  
        raise SubsNoFeedsFound(uri)
    elif len(feeds_found) > 1: 
        raise SubsMultipleFeedsFound(uri, feeds_found)
    else:
        feed_uri = feeds_found[0]
        if feed_uri in feeds:
            raise SubsAlreadySubscribed(feed_uri)
        feeds.append(feed_uri)
        return feed_uri

class EntryWrapper:
    def __init__(self, data, entry): 
        """
        Initialize the wrapper with feed and entry data.
        """
        self.data  = data
        self.feed  = data.feed
        self.entry = entry
        
        # Try to work out some sensible primary date for the entry, fall
        # back to the feed's date, and use the current time as a last resort.
        if entry.has_key("modified_parsed"):
            self.date = time.mktime(entry.modified_parsed)
        elif entry.has_key("issued_parsed"):
            self.date = time.mktime(entry.issued_parsed)
        elif self.feed.has_key("modified_parsed"):
            self.date = time.mktime(self.feed.modified_parsed)
        elif self.feed.has_key("issued_parsed"):
            self.date = time.mktime(self.feed.issued_parsed)
        else:
            self.date = time.time()

    def __cmp__(self, other):
        """
        Use the entry's date as the comparator for sorting & etc.
        """
        return other.date - self.date
    
    def __getitem__(self, name):
        """
        """
        # Handle access to feed data on keys starting with "feed."
        if name.startswith("feed."):
            return self.feed.get(name[5:], "").encode(UNICODE_ENC)
        # Handle access to entry data on keys starting with "entry."
        if name.startswith("entry."):
            return self.entry.get(name[6:], "").encode(UNICODE_ENC)
        # Handle a few more special-case keys.
        if name == "date":
            return time.strftime("%Y-%m-%d", time.localtime(self.date))
        if name == "time": 
            return time.strftime("%H:%M:%S", time.localtime(self.date))
        if name == "content":
            if self.entry.has_key("content"):
                return self.entry.content[0].value.encode(UNICODE_ENC)
            return ""

        # If all else fails, return an empty string.
        return ""
    
    def hash(self):
        """
        Come up with a unique identifier for this entry.
        """
        if self.entry.has_key('id'):
            return self.entry['id'].encode(UNICODE_ENC)
        else:
            m = md5.md5()
            for k in ('title', 'link', 'issued', 'modified', 'description'):
                m.update(self.entry.get(k,'').encode(UNICODE_ENC))
            return m.hexdigest()

