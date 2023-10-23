# Copyright (c) 2021, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import json

import sparrow


def execute():
	"""Convert Query Report json to support other content"""
	records = sparrow.get_all("Report", filters={"json": ["!=", ""]}, fields=["name", "json"])
	for record in records:
		jstr = record["json"]
		data = json.loads(jstr)
		if isinstance(data, list):
			# double escape braces
			jstr = f'{{"columns":{jstr}}}'
			sparrow.db.update("Report", record["name"], "json", jstr)
