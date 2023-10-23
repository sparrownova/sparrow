# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE
import sparrow


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	sparrow.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	sparrow.db.delete("Custom Field", {"dt": doctype})
	sparrow.clear_cache(doctype=doctype)
