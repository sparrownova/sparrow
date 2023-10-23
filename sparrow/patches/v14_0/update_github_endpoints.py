import json

import sparrow


def execute():
	if sparrow.db.exists("Social Login Key", "github"):
		sparrow.db.set_value(
			"Social Login Key", "github", "auth_url_data", json.dumps({"scope": "user:email"})
		)
