# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.delete_doc_if_exists("DocType", "User Permission for Page and Report")
