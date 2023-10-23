# Copyright (c) 2022, Sparrownova Technologies and Contributors
# MIT License. See license.txt

import sparrow


def execute():
	doctypes = sparrow.get_all("DocType", {"module": "Data Migration", "custom": 0}, pluck="name")
	for doctype in doctypes:
		sparrow.delete_doc("DocType", doctype, ignore_missing=True)

	sparrow.delete_doc("Module Def", "Data Migration", ignore_missing=True, force=True)
