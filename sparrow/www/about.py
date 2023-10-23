# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow

sitemap = 1


def get_context(context):
	context.doc = sparrow.get_cached_doc("About Us Settings")

	return context
