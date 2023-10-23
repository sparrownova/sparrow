# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class Milestone(Document):
	pass


def on_doctype_update():
	sparrow.db.add_index("Milestone", ["reference_type", "reference_name"])
