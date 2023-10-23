# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document
from sparrow.query_builder import Interval
from sparrow.query_builder.functions import Now


class ScheduledJobLog(Document):
	@staticmethod
	def clear_old_logs(days=90):
		table = sparrow.qb.DocType("Scheduled Job Log")
		sparrow.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))
