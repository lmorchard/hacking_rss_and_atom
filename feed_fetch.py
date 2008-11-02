#!/usr/bin/env python

import sys
from httpcache import HTTPCache

feed_uri     = sys.argv[1]
cache        = HTTPCache(feed_uri)
feed_content = cache.content()

print feed_content

