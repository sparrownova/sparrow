# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow.model.document import Document
from sparrow.utils.safe_exec import read_sql, safe_exec


class SystemConsole(Document):
	def run(self):
		sparrow.only_for("System Manager")
		try:
			sparrow.local.debug_log = []
			if self.type == "Python":
				safe_exec(self.console)
				self.output = "\n".join(sparrow.debug_log)
			elif self.type == "SQL":
				self.output = sparrow.as_json(read_sql(self.console, as_dict=1))
		except Exception:
			self.commit = False
			self.output = sparrow.get_traceback()

		if self.commit:
			sparrow.db.commit()
		else:
			sparrow.db.rollback()

		sparrow.get_doc(dict(doctype="Console Log", script=self.console)).insert()
		sparrow.db.commit()


@sparrow.whitelist()
def execute_code(doc):
	console = sparrow.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()


@sparrow.whitelist()
def show_processlist():
	sparrow.only_for("System Manager")

	return sparrow.db.multisql(
		{
			"postgres": """
			SELECT pid AS "Id",
				query_start AS "Time",
				state AS "State",
				query AS "Info",
				wait_event AS "Progress"
			FROM pg_stat_activity""",
			"mariadb": "show full processlist",
		},
		as_dict=True,
	)
