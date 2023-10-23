# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document
from sparrow.query_builder import Interval
from sparrow.query_builder.functions import Now


class ErrorLog(Document):
	def onload(self):
		if not self.seen and not sparrow.flags.read_only:
			self.db_set("seen", 1, update_modified=0)
			sparrow.db.commit()

	@staticmethod
	def clear_old_logs(days=30):
		table = sparrow.qb.DocType("Error Log")
		sparrow.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@sparrow.whitelist()
def clear_error_logs():
	"""Flush all Error Logs"""
	sparrow.only_for("System Manager")
	sparrow.db.truncate("Error Log")
