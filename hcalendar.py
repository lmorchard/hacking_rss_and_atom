#!/usr/bin/env python
"""
hackingfeeds/hcalendar.py

Parse hCalendar-formatted HTML to harvest iCalendar data.
"""
import sys, time, os, os.path
from datetime import datetime
from httpcache import HTTPCache
from HTMLParser import HTMLParser, HTMLParseError
from icalendar import Calendar, Event, TypesFactory 

def main():
    """
    Perform iCalendar to hCalendar rendering.
    """
    html_dir = len(sys.argv) > 1 and sys.argv[1] or 'hcal'
    ics_fout = len(sys.argv) > 2 and open(sys.argv[2], 'w') or sys.stdout

    # Parse a directory of HTML files for hCalendar events.
    hp = HCalendarParser()
    events = []
    for dirpath, dirnames, filenames in os.walk(html_dir):
        for fn in filenames:
            if fn.endswith(".html") or fn.endswith(".htm"):
                fp   = os.path.join(dirpath, fn)
                data = open(fp, 'r').read()
                events.extend(hp.parse(data))
    
    # Build a calendar from the parsed events and print the data
    cal = Calendar()
    for e in events: 
        cal.add_component(e)
    print cal.as_string()

class HCalendarParser(HTMLParser):
    """
    hCalendar parser, produces iCalendar Event objects.
    """
    CHUNKSIZE        = 1024
    ITEM_CLASS       = "vevent"
    PROPERTY_CLASSES = []

    def __init__(self):
        """Initialize the parser, using iCalendar properties."""
        self._types = TypesFactory()
        self.PROPERTY_CLASSES = \
            [ x.lower() for x in TypesFactory.types_map.keys() ]

    def parse(self, data):
        """Parse a string of HTML data, return items."""
        self.reset()
        try:
            self.feed(data)
        except HTMLParseError:
            pass
        self.finish()
        return self.items()

    def parse_uri(self, uri):
        """Parse HTML content at a URI, return items."""
        return self.parse(HTTPCache(uri).content())
           
    def items(self):
        """Build and return iCalendar Events for hCalendar items
        harvested from HTML concent."""

        events_out = []
        for item in self._items:

            # Build a new blank entry to receive the hCalendar data.
            event_out = Event()

            for name, val in item:
                try:
                    val = self._types.from_ical(name, val.strip())
                    if val: event_out.add(name, val)
                except:
                    pass

            # Add the finished entry to the list to be returned.
            events_out.append(event_out)

        return events_out
    
    def reset(self):
        """Initialize the parser state."""
        HTMLParser.reset(self)
        self._parse_stack   = [ [ {}, [], '' ] ]
        self._item_stack    = []
        self._items         = []

    def finish(self):
        """After parsing has finished, make sure last items get captured."""
        while len(self._item_stack):
            item = self._item_stack.pop()
            if len(item): self._items.append(item)

    def handle_starttag(self, tag, attrs_tup):
        """Handle start tags, maintaining tag content stacks and items."""
        # Initialize this level of the parsing stack.
        attrs   = dict(attrs_tup)
        classes = attrs.get('class', '').lower().split()
        self._parse_stack.append( [ attrs, classes, '' ] )

        # If this tag is the start of an item, initialize a new one.
        if self.ITEM_CLASS in classes: 
            self._item_stack.append([])
        
    def handle_endtag(self, tag):
        """Handle closing tags, capturing item properties as necessary."""
        # Pop the current tag's attributes and classes.
        attr, classes, value = self._parse_stack.pop()

        # Pop the current accumulation of character data from the stack,
        # but append it onto the parent's data
        value = self.decode_entities(value)
        self.handle_data(value)

        # Not currently tracking an item?  Skip processing, then.
        if not len(self._item_stack): return

        # Get the current working item
        curr_item = self._item_stack[-1]
        
        # If this type supports a uid, look for an id attribute
        if 'id' in attr and 'uid' in self.PROPERTY_CLASSES:
            curr_item.append( ('uid', attr['id']) )
        
        # Is this the end of an item?  If so, pop and add to the list.
        if self.ITEM_CLASS in classes:
            item = self._item_stack.pop()
            if len(item): self._items.append(item)
            return

        # Work through current tag's potential classes.
        for prop_class in classes:
            if prop_class in self.PROPERTY_CLASSES:

                if prop_class=='url' and 'href' in attr:
                    prop_val = attr['href']
                elif 'longdesc' in attr:
                    prop_val = attr['longdesc']
                elif 'alt' in attr:
                    prop_val = attr['alt']
                elif 'title' in attr:
                    prop_val = attr['title']
                else:
                    prop_val = value

                # Add the property name and value to the item.
                curr_item.append( (prop_class, prop_val.strip()) )

    # Basic character data accumulation handlers.
    def handle_data(self, data):      
        self._parse_stack[-1][2] += data
    def handle_entityref(self, data): 
        self._parse_stack[-1][2] += '&' + data + ';'
    handle_charref = handle_entityref

    # Utility function to resolve a limited set of HTML entities.
    ENTITIES = [ ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"'),
                 ('&apos;', "'"), ('&amp;', '&') ]
    def decode_entities(self, data):
        for f, t in self.ENTITIES: data = data.replace(f, t)
        return data

if __name__ == "__main__": main()
