# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	if sparrow.db.exists("DocType", "Event Producer"):
		sparrow.db.sql("""UPDATE `tabEvent Producer` SET api_key='', api_secret=''""")
	if sparrow.db.exists("DocType", "Event Consumer"):
		sparrow.db.sql("""UPDATE `tabEvent Consumer` SET api_key='', api_secret=''""")
