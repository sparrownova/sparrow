# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class WebhookRequestLog(Document):
	@staticmethod
	def clear_old_logs(days=30):
		from sparrow.query_builder import Interval
		from sparrow.query_builder.functions import Now

		table = sparrow.qb.DocType("Webhook Request Log")
		sparrow.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))
