"""
htmlmetalib.py

Provides HTMLMetaDoc, an easy way to access metadata in 
HTML files.
"""
import sys, time, os, os.path
from HTMLParser import HTMLParser, HTMLParseError

def main():
    """
    Test everything out by finding all HTML in a path given as
    a command line argument.  Get metadata for all HTML found 
    and print titles, paths, and descriptions.
    """
    docs = findHTML(sys.argv[1])
    tmpl = "%(title)s (%(path)s)\n\t%(description)s"
    print "\n".join([tmpl % x for x in docs])

def findHTML(path):
    """
    Recursively search for all files ending in .html and .htm
    in at a given path.  Create HTMLMetaDoc objects for all and
    return the bunch.
    """
    docs = []
    for dirpath, dirnames, filenames in os.walk(path):
        for fn in filenames:
            if fn.endswith(".html") or fn.endswith(".htm"):
                fp  = os.path.join(dirpath, fn)
                doc = HTMLMetaDoc(fp)
                docs.append(doc)
    return docs

class HTMLMetaDoc:
    """
    Encapsulates HTML documents in files, extracting metadata 
    on initialization.
    """
    def __init__(self, filepath):
        self.title       = ''
        self.content     = ''
        self.description = ''

        self.path = filepath

        s = os.stat(filepath)
        self.modified = s.st_mtime
        
        parser = HTMLMetaParser()
        parser.parse_file(self, open(filepath))

    def __getitem__(self, name):
        """
        Translate map-like access into attribute fetch for templates.
        """
        return getattr(self, name)

    def __cmp__(self, other):
        """
        Compare for sort order on modfied dates.
        """
        return other.modified - self.modified
    
class _HTMLMetaParserFinished(Exception):
    """
    Private exception, raised when the parser has finished with
    the HTML <head> contents and isn't interested in any more data.
    """
    pass

class HTMLMetaParser(HTMLParser):
    """
    Parses HTML to extract the page title and description.
    """
    CHUNKSIZE = 1024
    
    def reset(self):
        """
        Initialize the parser state.
        """
        HTMLParser.reset(self)
        self.curr_doc   = None
        self.curr_attrs = {}
        self.curr_val   = ''
        self.in_head    = False
        self.in_body    = False
        self.parse_body = True

    def reset_doc(self, doc):
        """
        Reset the parser and set the current doc to me populated.
        """
        self.reset()
        self.curr_doc = doc

    def parse_file(self, doc, fin):
        """
        Parse through the contents of a given file-like object.
        """
        self.reset_doc(doc)
        while True:
            try:
                data = fin.read(self.CHUNKSIZE)
                if len(data) == 0: break
                self.feed(data)
            except HTMLParseError:
                pass
            except _HTMLMetaParserFinished:
                break
           
    def handle_starttag(self, tag, attrs_tup):
        """
        Handle start tags, watch for and flag beginning of <head>
        section, process <meta> tags inside <head> section.
        """
        curr_val = self.decode_entities(self.curr_val.strip())
        self.curr_val = ''
        attrs = dict(attrs_tup)
        
        if tag == 'head': 
            self.in_head = True
            
        elif tag == 'body':
            self.in_body = True
            
        elif self.in_head:
            if tag == "meta":
                meta_name    = attrs.get('name', '').lower()
                meta_content = attrs.get('content', '')
                if meta_name == "description":
                    self.curr_doc.description = meta_content

        elif self.in_body:
            attrs_str = ' '.join([ '%s="%s"' % x for x in attrs_tup ])
            self.curr_doc.content += '%s<%s %s>' % \
                                     ( curr_val, tag, attrs_str )
        
    def handle_endtag(self, tag):
        """
        Handle end tags, watch for finished <title> tag inside <head>,
        and raise an exception when the end of the <head> section is
        found.
        """
        curr_val = self.decode_entities(self.curr_val.strip())
        self.curr_val = ''
        
        if self.in_head:
            if tag == "title": 
                self.curr_doc.title = curr_val
        
        if tag == 'head': 
            self.in_head = False
            if not self.parse_body:
                raise _HTMLMetaParserFinished()
        
        if tag == 'body':
            self.curr_doc.content += curr_val
            raise _HTMLMetaParserFinished()
        
        if self.in_body:
            self.curr_doc.content += '%s</%s>' % ( curr_val, tag )

    def handle_data(self, data):
        self.curr_val += data
    def handle_entityref(self, data): 
        self.curr_val += '&' + data + ';'
    handle_charref = handle_entityref

    def decode_entities(self, data):
        data = data.replace('&lt;', '<')
        data = data.replace('&gt;', '>')
        data = data.replace('&quot;', '"')
        data = data.replace('&apos;', "'")
        data = data.replace('&amp;', '&')
        return data
    
if __name__ == "__main__": main()
