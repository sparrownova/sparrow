# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.delete_doc_if_exists("DocType", "User Permission for Page and Report")
