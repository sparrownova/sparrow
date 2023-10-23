# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.search.full_text_search import FullTextSearch
from sparrow.search.website_search import WebsiteSearch
from sparrow.utils import cint


@sparrow.whitelist(allow_guest=True)
def web_search(query, scope=None, limit=20):
	limit = cint(limit)
	ws = WebsiteSearch(index_name="web_routes")
	return ws.search(query, scope, limit)
