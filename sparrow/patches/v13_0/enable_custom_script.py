# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	"""Enable all the existing Client script"""

	sparrow.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
