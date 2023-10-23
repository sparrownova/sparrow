# Copyright (c) 2015, Sparrownova Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document
from sparrow.query_builder import Interval
from sparrow.query_builder.functions import Now


class ErrorSnapshot(Document):
	no_feed_on_delete = True

	def onload(self):
		if not self.parent_error_snapshot:
			self.db_set("seen", 1, update_modified=False)

			for relapsed in sparrow.get_all("Error Snapshot", filters={"parent_error_snapshot": self.name}):
				sparrow.db.set_value("Error Snapshot", relapsed.name, "seen", 1, update_modified=False)

			sparrow.local.flags.commit = True

	def validate(self):
		parent = sparrow.get_all(
			"Error Snapshot",
			filters={"evalue": self.evalue, "parent_error_snapshot": ""},
			fields=["name", "relapses", "seen"],
			limit_page_length=1,
		)

		if parent:
			parent = parent[0]
			self.update({"parent_error_snapshot": parent["name"]})
			sparrow.db.set_value("Error Snapshot", parent["name"], "relapses", parent["relapses"] + 1)
			if parent["seen"]:
				sparrow.db.set_value("Error Snapshot", parent["name"], "seen", 0)

	@staticmethod
	def clear_old_logs(days=30):
		table = sparrow.qb.DocType("Error Snapshot")
		sparrow.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))
