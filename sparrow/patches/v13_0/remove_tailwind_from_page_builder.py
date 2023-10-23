# Copyright (c) 2020, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	sparrow.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	sparrow.delete_doc("Web Template", "Footer Horizontal", force=1)
