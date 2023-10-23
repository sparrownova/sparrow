# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class DefaultValue(Document):
	pass


def on_doctype_update():
	"""Create indexes for `tabDefaultValue` on `(parent, defkey)`"""
	sparrow.db.commit()
	sparrow.db.add_index(
		doctype="DefaultValue",
		fields=["parent", "defkey"],
		index_name="defaultvalue_parent_defkey_index",
	)

	sparrow.db.add_index(
		doctype="DefaultValue",
		fields=["parent", "parenttype"],
		index_name="defaultvalue_parent_parenttype_index",
	)
