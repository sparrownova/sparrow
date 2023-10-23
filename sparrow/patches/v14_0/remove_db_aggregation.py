import re

import sparrow
from sparrow.query_builder import DocType


def execute():
	"""Replace temporarily available Database Aggregate APIs on sparrow (develop)

	APIs changed:
	        * sparrow.db.max => sparrow.qb.max
	        * sparrow.db.min => sparrow.qb.min
	        * sparrow.db.sum => sparrow.qb.sum
	        * sparrow.db.avg => sparrow.qb.avg
	"""
	ServerScript = DocType("Server Script")
	server_scripts = (
		sparrow.qb.from_(ServerScript)
		.where(
			ServerScript.script.like("%sparrow.db.max(%")
			| ServerScript.script.like("%sparrow.db.min(%")
			| ServerScript.script.like("%sparrow.db.sum(%")
			| ServerScript.script.like("%sparrow.db.avg(%")
		)
		.select("name", "script")
		.run(as_dict=True)
	)

	for server_script in server_scripts:
		name, script = server_script["name"], server_script["script"]

		for agg in ["avg", "max", "min", "sum"]:
			script = re.sub(f"sparrow.db.{agg}\\(", f"sparrow.qb.{agg}(", script)

		sparrow.db.update("Server Script", name, "script", script)
