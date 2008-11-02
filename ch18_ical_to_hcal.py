#!/usr/bin/env python
"""
ch18_ical_to_hcal.py

Render iCalendar as hCalendar-formatted HTML.
"""
import os, sys
from md5 import md5
from httpcache import HTTPCache
from icalendar import Calendar, Event

HTML_DIR = "hcal"
ICS_URL  = "http://icalx.com/public/peterpqa/US-Practical.ics"

HEVENT_TMPL = u"""
    <html>
        <head>
            <title>%(dtstart:date:%A, %B %d, %Y)s: %(summary)s</title>
            <meta name="description" content="%(description)s" />
        </head>
        <body>
            <div class="vcalendar">
                <div class="vevent" id="%(uid)s">
                    <abbr class="dtstart" title="%(dtstart:encoded)s">
                        %(dtstart:date:%A, %B %d, %Y)s
                    </abbr>:
                    <b class="summary">%(summary)s</b>
                    <blockquote class="description">
                        %(description)s
                    </blockquote>
                    <abbr class="dtend" title="%(dtend:encoded)s"
                          style="display:none" />
                </div>
            </div>
        </body>
    </html>
"""

def main():
    """
    Perform iCalendar to hCalendar rendering.
    """
    # Establish the calendar URL and output file.
    ics_url   = len(sys.argv) > 1 and sys.argv[0] or ICS_URL
    html_dir = len(sys.argv) > 2 and sys.argv[1] or HTML_DIR
        
    # Get the calendar via URL and parse the data
    cal = Calendar.from_string(HTTPCache(ics_url).content())

    # Create HTML_DIR if it doesn't already exist
    if not os.path.exists(html_dir): os.makedirs(html_dir)
    
    # Process calendar components.
    for event in cal.walk():
        
        # Skip this calendar component if it's not an event.
        if not type(event) is Event: continue
        
        # Summarize the event data, make a hash, build a filename.
        hash_src = ','.join(['%s=%s' % x for x in event.items()])
        hash     = md5(hash_src).hexdigest()
        hcal_fn  = os.path.join(html_dir, '%s.html' % hash)

        # Build the hCalendar content and write out to file.
        hcal_out = HEVENT_TMPL % ICalTmplWrapper(event)
        open(hcal_fn, 'w').write(hcal_out)

class ICalTmplWrapper:
    """
    Formatting helper class for iCalendar objects.
    """
    
    def __init__(self, obj):
        """Initialize wrapper with an iCal obj instance."""
        self.obj = obj
        
    def __getitem__(self, key):
        """Provides simple formatting options for dates and encoding."""
        # Get the name and optional formatting type from format key
        name, fmt = (':' in key) and key.split(':', 1) or (key, None)

        # If no such key in obj, return blank.
        if not self.obj.has_key(name): return ''
            
        # No special formatting, return decoded value.
        if fmt is None: return self.obj.decoded(name)
        
        # 'encoded' formatting, return the encoded value.
        elif fmt == 'encoded': return self.obj[name]

        # 'date' formatting, so assume this value is a datetime
        # and return formatted according to supplied option.
        elif fmt.startswith('date:'):
            fmt, date_fmt = fmt.encode().split(":",1)
            data = self.obj.decoded(name)
            return data.strftime(date_fmt)

if __name__=='__main__': main()

