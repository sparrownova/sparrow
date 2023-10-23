# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class CommunicationLink(Document):
	pass


def on_doctype_update():
	sparrow.db.add_index("Communication Link", ["link_doctype", "link_name"])
