#!/usr/bin/env python
"""
amazonlib

Tools for generating feeds from Amazon Web Service requests.
"""
import md5, urllib, xmltramp
from scraperlib import FeedEntryDict, Scraper

class AmazonScraper(Scraper):
    """
    Generates feeds from lists of products from Amazon Web 
    Services queries.
    """
    AWS_URL = "http://webservices.amazon.com/onca/xml"

    ITEM_TRACK = (
        'ASIN', 
        'ItemAttributes.ListPrice.FormattedPrice'
    )

    TAG_DOMAIN = "www.decafbad.com"
    TAG_DATE   = "2005-03-06"
    STATE_FN   = "amazon_wishlist_state"

    ATOM_ENTRY_TMPL = """
        <entry>
            <title>%(entry.title)s</title>
            <author>
                <name>%(entry.author.name)s</name>
            </author>
            <link rel="alternate" type="text/html"
                  href="%(entry.link)s" />
            <issued>%(entry.issued)s</issued>
            <modified>%(entry.modified)s</modified>
            <id>%(entry.id)s</id>
            <summary type="text/html" 
                     mode="escaped">%(entry.summary)s</summary>
        </entry>
    """

    TITLE_TMPL = \
        "[%(ItemAttributes.ProductGroup)s] " + \
        "(%(ItemAttributes.ListPrice.FormattedPrice)s) " + \
        "%(ItemAttributes.Title)s - %(ItemAttributes.Author)s"
    
    SUMMARY_TMPL = """
        <b>%(ItemAttributes.Title)s</b><br />
        <i>%(ItemAttributes.Author)s</i></br />
        <img src="%(MediumImage.URL)s" /><br />
    """
    
    def produce_entries(self):
        """
        Produce feed entries from Amazon product item data.
        """
        entries = []

        all_items = self.fetch_items()
        
        # Run through all fetched items, building entries
        for item in all_items:
            
            # Wrap the item in a template-friendly object
            tmpl_item = TrampTmplWrapper(item)
            
            # Build an empty entry object
            entry = FeedEntryDict(date_fmt=self.date_fmt)
            
            # Generate an ID for this entry based on tracked data
            m = md5.md5()
            for k in self.ITEM_TRACK:
                m.update(tmpl_item[k])
            entry['id'] = state_id = "tag:%s,%s:%s" % \
                (self.TAG_DOMAIN, self.TAG_DATE, m.hexdigest())

            # Use the item detail URL for entry link
            entry['link'] = tmpl_item['DetailPageURL']
            
            # Use the author, artist, or actor name for item 
            # and entry author
            authors = []
            for k in ( 'Author', 'Artist', 'Actor' ):
                v = tmpl_item['ItemAttributes.%s' % k]
                if v: authors.append(v)
            entry['author.name'] = ", ".join(authors)
           
            # Build entry title and summary from string templates
            entry['title']   = self.TITLE_TMPL % tmpl_item
            entry['summary'] = self.SUMMARY_TMPL % tmpl_item
            
            # Append completed entry to list
            entries.append(entry)

        return entries

class TrampTmplWrapper:
    """
    Wrapper to provide dictionary-style access to xmltramp
    nodes with dotted paths, for use in string templates.
    """
    def __init__(self, node):
        """
        Initialize with an xmltramp node.
        """
        self.node = node

    def __getitem__(self, path):
        """
        Walk through xmltramp child nodes, given a dotted path.
        Returns an empty string on a path not found.
        """
        try:
            # Walk through the path nodes, return end node as string.
            curr = self.node
            for p in path.split('.'): 
                curr = getattr(curr, p)
            return str(curr)
        
        except TypeError:
            # HACK: Not intuitive, but this is what xmltramp throws
            # for an attribute not found.
            return ""

