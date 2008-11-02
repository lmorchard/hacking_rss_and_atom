#!/usr/bin/env python
"""
imconn.py

This is a module providing IM server connections
with a built-in echo chatbot for testing. 
"""
import sys, os, time, select
from toc import TocTalk
import xmpp

def main():
    AIM_USER, AIM_PASSWD = "your_name", "password"
    JAB_USER, JAB_PASSWD = "your_name@jabber.org", "password"

    connections = [
        AIMConnection(AIM_USER, AIM_PASSWD, echo),
        JabberConnection(JAB_USER, JAB_PASSWD, echo)
    ]
    
    for c in connections: c.connect()
    while 1:
        for c in connections: c.runOnce()
        time.sleep(0.1)

def echo(conn, from_nick, msg):
    print "%s || %s: %s" % (conn, from_nick, msg)
    conn.sendIM(from_nick, "Is there an echo in here? %s" % msg)

class AIMConnection(TocTalk):
    """
    Encapsulate a connection to the AOL Instant Messenger service.
    """
    
    def __init__(self, user, passwd, recv_func=None):
        """
        Initialize the connection both as a TocTalk subclass.
        """
        TocTalk.__init__(self, user, passwd)
        self._recv_func = recv_func
        self._ready     = False
        self._debug     = 0
    
    def connect(self):
        """
        Connect to the AIM service.  Overrides the behavior of the 
        superclass by waiting until login has completed before returning.
        """
        # Start the connection & login process to AIM
        TocTalk.connect(self)
        
        # Set socket to non-blocking, to be multitasking-friendly
        self._socket.setblocking(0)
        
        # Process events until login is a success
        while not self._ready:
            self.runOnce()
            time.sleep(0.1)
    
    def start(self):
        """
        This method gets called by the superclass when the connection is 
        ready for use.
        """
        self._ready = True
    
    def runOnce(self):
        """
        Perform one processing step of AIM events.
        """
        # Check to see if there's anything to read on the AIM socket, 
        # without blocking.  Return if there's nothing yet.
        r, w, e = select.select([self._socket],[],[],0)
        if len(r) > 0:
            # Try receiving an event from AIM, process it if found.
            event = self.recv_event()
            if event: self.handle_event(event)
        
    def sendIM(self, to_name, msg):
        """
        Given an destination name and a message, send it off.
        """
        self.do_SEND_IM(to_name, msg)

    def on_IM_IN(self, data):
        """
        This method is called by the superclass when a new IM arrives.
        Process the IM data and trigger the callback initialized with this
        connection.
        """
        # This is a quick way to get the first two colon-delimited 
        # fields, in case the message itself contains colons
        from_nick, auto_resp, msg = data.split(':',2)
        if self._recv_func:
            self._recv_func(self, from_nick, self.strip_html(msg)) 

class JabberConnection:
    """
    Encapsulate a connection to the Jabber instant messenger service.
    """
    
    def __init__(self, user, passwd, recv_func=None):
        """
        Initialize the Jabber connection.
        """
        self._user      = user
        self._passwd    = passwd
        self._recv_func = recv_func
        self._jid       = xmpp.protocol.JID(self._user)
        self._cl        = xmpp.Client(self._jid.getDomain(),debug=[])

    def connect(self):
        """
        Connect to Jabber, authenticate, set up callbacks.
        """
        self._cl.connect()
        self._cl.auth(self._jid.getNode(), self._passwd)
        self._cl.RegisterHandler('message', self._messageCB)
        self._cl.RegisterHandler('presence', self._presenceCB)
        self._cl.sendInitPresence()
    
    def runOnce(self):
        """
        Process one event handler loop.
        """
        self._cl.Process(1)
        
    def sendIM(self, to_name, msg):
        """
        Send off an instant message.
        """
        self._cl.send(xmpp.protocol.Message(to_name, msg))

    def __del__(self):
        """
        Try cleaning up in the end by signalling that this connection
        is unavailable.
        """
        try: self._cl.sendPresence(typ="unavailable")
        except: pass
            
    def _presenceCB(self, conn, pres):
        """
        Respond to presence events.  If someone tries subscribing to this
        connection's presence, automatically respond by allowing it. 
        """
        if pres.getType() == 'subscribe':
            self._cl.sendPresence(jid=pres.getFrom(), typ='subscribed')
        
    def _messageCB(self, conn, mess):
        """
        Respond to message events.  This method calls the callback
        given at connection initialization to handle the message data.
        """
        if self._recv_func:
            text = mess.getBody()
            user = mess.getFrom().getStripped()
            self._recv_func(self, user, text)

if __name__ == "__main__": main()
