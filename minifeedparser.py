"""
minifeedparser.py

A feature-light multi-format syndication feed parser, intended to do
a reasonable job extracting data from RSS 1.0, RSS 2.0, and Atom 0.3 feeds.
"""
from sgmllib   import SGMLParser
from httpcache import HTTPCache

def parse(feed_uri):
    """
    Create a throwaway parser object and return the results of 
    parsing for the given feed URL
    """
    return MiniFeedParser().parse(feed_uri)

class MiniFeedParser(SGMLParser):

    def parse(self, feed_uri):
        """Given a URI to a feed, fetch it and return parsed data."""
        
        cache        = HTTPCache(feed_uri)
        feed_content = cache.content()
        
        self.reset()
        self.feed(feed_content)
        
        return {
            'version'  : self._version,
            'feed'     : self._feed,
            'entries'  : self._entries
        }
        
    def reset(self):
        """Initialize the parser state."""
        self._version = "unknown"
        self._feed    = {
            'title'    : '',
            'link'     : '',
            'author'   : '',
            'modified' : '',
        }
        self._entries = []
        
        self.in_entry      = False
        self.current_tag   = None
        self.current_attrs = {}
        self.current_value = ''
        
        SGMLParser.reset(self)

    def start_rdf(self, attrs_tuples):
        """Handle RSS 1.0 feed start tag."""
        self._version = "rss10"
    
    def start_rss(self, attrs_tuples):
        """Handle RSS 2.0 feed start tag."""
        attrs = dict(attrs_tuples)
        if attrs.get('version', '???') == '2.0':
            self._version = "rss20"
        else:
            self._version = "rss??"

    def start_feed(self, attrs_tuples):
        """Handle Atom 0.3 feed start tag."""
        attrs = dict(attrs_tuples)
        if attrs.get('version', '???') == '0.3':
            self._version = "atom03"
        else:
            self._version = "atom??"
    
    def start_entry(self, attrs):
        new_entry = {
            'title'   : '',
            'link'    : '',
            'modified': '',
            'summary' : '',
            'content' : '',
        }
        self._entries.append(new_entry)
        self.in_entry = True

    def end_entry(self):
        # OK, we're out of the RSS item
        self.in_entry = False

    start_item = start_entry
    end_item   = end_entry

    def unknown_starttag(self, tag, attrs):
        self.current_tag   = tag
        self.current_attrs = dict(attrs)
        
        if 'atom' in self._version:
            if tag == 'link':
                current_value = self.current_attrs.get('href', '')
                if self.in_entry:
                    self._entries[-1]['link'] = current_value
                else:
                    self._feed['link'] = current_value

    def handle_data(self, data):
        # buffer all text data
        self.current_value += data

    def handle_entityref(self, data):
        # buffer all entities
        self.current_value += '&' + data + ';'
    handle_charref = handle_entityref

    def unknown_endtag(self, tag):
        current_value     = self.decode_entities(self.current_value.strip())
        current_prop_name = self.translate_prop_name(tag)
        
        if self.in_entry:
            self._entries[-1][current_prop_name] = current_value
        else:
            self._feed[current_prop_name] = current_value

        self.current_value = ''

    def decode_entities(self, data):
        data = data.replace('&lt;', '<')
        data = data.replace('&gt;', '>')
        data = data.replace('&quot;', '"')
        data = data.replace('&apos;', "'")
        data = data.replace('&amp;', '&')
        return data
    
    def translate_prop_name(self, name):
        map = self.PROP_MAPS[self._version]
        if self.in_entry and map.has_key('entry'):
            return map['entry'].get(name, name)
        if not self.in_entry and map.has_key('feed'):
            return map['feed'].get(name, name)
        return name
    
    PROP_MAPS = {
        'rss10' : {
            'feed'  : {
                'dc:date'        : 'modified',
                'webmaster'      : 'author',
                'managingeditor' : 'author',
                'guid'           : 'id',
            },
            'entry' : {
                'dc:date'        : 'modified',
                'description'    : 'summary',
                'guid'           : 'id',
            }
        },
        'rss20' : {
            'feed'  : {
                'pubdate'        : 'modified',
                'webmaster'      : 'author',
                'managingeditor' : 'author',
                'guid'           : 'id',
            },
            'entry' : {
                'pubdate'        : 'modified',
                'description'    : 'summary',
                'guid'           : 'id',
            }
        },
        'atom03' : {
        },
    }
    PROP_MAPS['atom??'] = PROP_MAPS['atom03']
    PROP_MAPS['rss??']  = PROP_MAPS['rss20']
    
