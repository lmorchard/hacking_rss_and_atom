#!/usr/bin/env python
"""
ch18_feed_to_ical.py

Produce iCalendar data from a syndication feed.
"""
import os, sys, feedparser
from hcalendar import HCalendarParser
from icalendar import Calendar, Event, TypesFactory

#FEED_URL = "http://localhost/~deusx/hackingfeeds/src/mod-event.atom" 
FEED_URL = "feed://./mod-event.atom" 
ICS_FN   = "feed_events.ics"

def main():
    """
    Process calendar data present in a feed to build iCalendar events.
    """
    # Grab the feed for processing
    feed_url = len(sys.argv) > 1 and sys.argv[1] or FEED_URL
    ics_fn   = len(sys.argv) > 2 and sys.argv[2] or ICS_FN

    # Get the feed, create a new calendar and an hCalendar parser.
    feed  = feedparser.parse(feed_url)
    cal   = Calendar()
    hp    = HCalendarParser()
    types = TypesFactory()

    # Scan all the feed entries for calendar events.
    for entry in feed.entries:
        
        # First, check for any hCalendar events in the feed summary
        # content.
        if 'summary' in entry:
            # Attempt to parse the entry summary for hCalendar events.
            events = hp.parse(entry['summary'])
            if events:
                # Add all the events, then continue on to next entry.
                for e in events: cal.add_component(e)
                continue
                  
        # Here's an attempt to map feedparser entry metadata
        # to event properties.
        entry_to_event = [
           ( 'link',         'url' ),
           ( 'title',        'summary' ),
           ( 'summary',      'description' ),
           ( 'ev_startdate', 'dtstart' ),
           ( 'ev_enddate',   'dtend' ),
           ( 'ev_location',  'location' ),
           ( 'ev_organizer', 'organizer' ),
           ( 'ev_type',      'type' ),
        ]
        
        # If no events found in entry content, try constructing one from
        # feed metadata values.
        event = Event()
        for entry_key, event_key in entry_to_event:
            
            # Check to see this metadata key is in the entry.
            if entry_key in entry:
                entry_val = entry[entry_key]

                # HACK: Get rid of date and time field separators to
                # better match iCalendar's time format.
                if event_key.startswith('dt'):
                    entry_val = entry_val.replace('-','').replace(':','')
            
                # Convert the entry metadata value to a event date type
                # and add it to the event.
                val = types.from_ical(event_key, entry_val.encode('UTF-8'))
                event.add(event_key, val)

        # Add the event to the calendar after building it.
        cal.add_component(event)

    # Write the iCalendar file out to disk.
    open(ics_fn, "w").write(cal.as_string())

if __name__ == '__main__': main()
