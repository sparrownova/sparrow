# Copyright (c) 2020, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


def execute():
	sparrow.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	sparrow.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	sparrow.delete_doc("DocType", "Package Publish Target", ignore_missing=True)
