#!/usr/bin/env python
"""
agg06_aggbot.py

Interactive IM bot which manages feed subscriptions and polls feeds 
on demand.
"""
import time

from imconn import AIMConnection, JabberConnection
from agglib import *

AIM_OWNER = "your_name"
AIM_USER   = "your_name"
AIM_PASSWD = "your_password"

JAB_OWNER = "your_name@jabber.org" 
JAB_USER   = "your_name@jabber.org"
JAB_PASSWD = "your_password"

FEEDS_FN    = "feeds.txt"
FEED_DB_FN  = "feeds_db"
ENTRY_DB_FN = "entry_seen_db"

def main(): 
    """
    Create a new bot, add some IM network connections, and fire it up.
    """
    bot = AggBot(FEEDS_FN, FEED_DB_FN, ENTRY_DB_FN)
    bot.addConnection(AIMConnection, AIM_OWNER, AIM_USER, AIM_PASSWD)
    bot.addConnection(JabberConnection, JAB_OWNER, JAB_USER, JAB_PASSWD)
    bot.go()

class AggBot:
    """
    This is a feed aggregator bot that accepts commands via instant message.
    """
    
    IM_CHUNK   = 7

    FEED_HDR_TMPL = """\n<a href="%(feed.link)s"><u>%(feed.title)s</u></a>\n\n"""
    ENTRY_TMPL    = """    * <a href="%(entry.link)s">%(entry.title)s</a>\n"""
    MSG_TMPL      = "%s"
    #FEED_HDR_TMPL = """\n%(feed.title)s - %(feed.link)s\n\n"""
    #ENTRY_TMPL    = """    * %(entry.title)s - %(entry.link)s\n\n"""
    #MSG_TMPL      = "%s"

    def __init__(self, feeds_fn, feed_db_fn, entry_db_fn):
        """
        Initialize the bot object, open aggregator databases, load up 
        subscriptions.
        """
        self.connections, self.owners, self.running = [], [], False
        self.feeds_fn = feeds_fn
        self.feed_db_fn = feed_db_fn
        self.entry_db_fn = entry_db_fn
    
    def __del__(self):
        """
        Object destructor - make sure the aggregator databases get closed.
        """
        try: closeDBs(self.feed_db, self.entry_db)
        except: pass
        
    def addConnection(self, conn_cls, owner, user, passwd):
        """
        Given a connection class, owner screen name, and a user/password,
        create the IM connection and store it away along with the owner 
        user.
        """
        self.connections.append(conn_cls(user, passwd, self.receiveIM))
        self.owners.append(owner)

    def getOwner(self, conn):
        """
        For a given connection, return the owner's screen name.
        """
        return self.owners[self.connections.index(conn)]
    
    def connect(self):
        """
        Cause all the IM connections objects connect to their networks.
        """
        for c in self.connections: c.connect()

    def runOnce(self):
        """
        Run through one event loop step.
        """
        for c in self.connections: c.runOnce()

    def go(self):
        """
        Connect and run event loop, until running flag set to false.
        """
        try:
            self.feed_db, self.entry_db = openDBs(self.feed_db_fn, self.entry_db_fn)
            self.feeds = loadSubs(self.feeds_fn)
            self.running = True
            self.connect()
            while self.running:
                self.runOnce()
                time.sleep(0.1)
        finally:
            try: closeDBs(self.feed_db, self.entry_db)
            except: pass
    
    def stop(self):
        """
        Stop event loop by setting running flag to false.
        """
        self.running = False

    def receiveIM(self, conn, from_name, msg):
        """
        Process incoming messages as commands.  Message is space-delimited,
        command is first word found, everything else becomes parameters.
        Commands are handled by methods with 'cmd_' prepended to the name
        of the command.
        """
        try:
            owner = self.getOwner(conn)
            if from_name != owner:
                # Don't listen to commands from anyone who's not the bot owner. 
                conn.sendIM(from_name, "I don't talk to strangers.")
            else:
                if msg == "":
                    # Check for empty messages.
                    conn.sendIM(from_name, "Did you say something?")
                else:
                    # Try to parse the message.  Space-delimited, first
                    # part of message is the command, everything else is
                    # optional parameters.
                    try:
                        fs = msg.index(" ")
                        cmd, args = msg[:fs], msg[fs+1:].split(" ")
                    except:
                        cmd, args = msg, []

                    # Look for a method in this class corresponding to 
                    # command prepended with 'cmd_'.  If found, execute it.
                    cmd_func_name = 'cmd_%s' % cmd
                    if hasattr(self, cmd_func_name):
                        getattr(self, cmd_func_name)(conn, from_name, args)
                    else:
                        conn.sendIM(from_name, "I don't understand you.")
        
        except Exception, e:
            # Something unexpected happened, so make some attempt to 
            # say what.
            conn.sendIM(from_name, "That last message really confused me! (%s)" % e)

    def getSubscriptionURI(self, sub_arg):
        """
        Utility function which allows reference to a subscription either by
        integer index in list of subscriptions, or by direct URI reference.
        """
        try:
            sub_num = int(sub_arg)
            return self.feeds[sub_num]
        except ValueError:
            return sub_arg

    def pollFeed(self, conn, from_name, sub_uri):
        """
        Perform a feed poll and send the new entries as messages.
        """
        entries = getNewFeedEntries([sub_uri], self.feed_db, 
            self.entry_db)
        if len(entries) > 0:
            sendEntriesViaIM(conn, from_name, entries, self.IM_CHUNK, 
                    self.FEED_HDR_TMPL, self.ENTRY_TMPL, self.MSG_TMPL)
        else:
            conn.sendIM(from_name, "No new entries available.")
            
    def cmd_signoff(self, conn, from_name, args):
        """
        signoff: Command the bot to sign off and exit the program.
        """
        conn.sendIM(from_name, "Okay, signing off now.")
        self.stop()
        
    def cmd_list(self, conn, from_name, args):
        """
        list: List all subscriptions by index and URI.
        """
        out = []
        out.append("You have the following subscriptions:")
        for i in range(len(self.feeds)):
            out.append("   %s: %s" % (i, self.feeds[i]))
        conn.sendIM(from_name, "\n".join(out))

    def cmd_unsubscribe(self, conn, from_name, args):
        """
        unsubscribe <sub>: Unsubscribe from a feed by index or URI.
        """
        try:
            sub_uri = self.getSubscriptionURI(args[0])
            unsubscribeFeed(self.feeds, sub_uri)
            saveSubs(self.feeds_fn, self.feeds)
            conn.sendIM(from_name, "Unsubscribed from %s" % sub_uri)
                
        except SubsNotSubscribed:
            conn.sendIM(from_name, "Not subscribed to that feed.")

        except IndexError:
            conn.sendIM(from_name, "Need a valid number or a URI.")
        
    def cmd_subscribe(self, conn, from_name, args):
        """
        subscribe <uri>: Use the feedfinder module to find a feed URI
        and add a subscription, if possible.  Reports exceptions such as
        no feeds found, multiple feeds found, or already subscribed.
        """
        try:
            feed_uri = subscribeFeed(self.feeds, args[0])
            saveSubs(self.feeds_fn, self.feeds)
            conn.sendIM(from_name, "Subscribed to %s" % feed_uri)
        except SubsNoFeedsFound:
            conn.sendIM(from_name, "Sorry, no feeds found at %s" % args[0])
        except SubsAlreadySubscribed:
            conn.sendIM(from_name, "You're already subscribed.")
        except SubsMultipleFeedsFound, e:
            feeds_found = e.getFeeds()
            out = ['Multiple feeds found, please pick one:']
            for f in feeds_found:
                out.append("    %s" % f)
            conn.sendIM(from_name, "\n".join(out))

        
    def cmd_poll(self, conn, from_name, args):
        """
        poll <index or URI>: Perform an on-demand poll of a feed.
        """
        try:
            sub_uri = self.getSubscriptionURI(args[0])
            self.pollFeed(conn, from_name, sub_uri)
        except IndexError:
            conn.sendIM(from_name, "Need a valid number or a URI.")
        
    def cmd_pollsubs(self, conn, from_name, args):
        """
        pollsubs: Perform an on-demand poll of all subscriptions.
        """
        conn.sendIM(from_name, "Polling all subscriptions...")
        for feed in self.feeds: 
            conn.sendIM(from_name, "Polling %s" % feed)
            self.pollFeed(conn, from_name, feed)
            
if __name__ == "__main__": main()
