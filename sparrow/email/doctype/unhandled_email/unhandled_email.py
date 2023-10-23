# Copyright (c) 2015, Sparrownova Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class UnhandledEmail(Document):
	pass


def remove_old_unhandled_emails():
	sparrow.db.delete(
		"Unhandled Email", {"creation": ("<", sparrow.utils.add_days(sparrow.utils.nowdate(), -30))}
	)
