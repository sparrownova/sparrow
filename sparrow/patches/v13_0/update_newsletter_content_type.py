# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.reload_doc("email", "doctype", "Newsletter")
	sparrow.db.sql(
		"""
		UPDATE tabNewsletter
		SET content_type = 'Rich Text'
	"""
	)
