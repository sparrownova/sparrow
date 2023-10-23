import json

import sparrow


def execute():
	"""Handle introduction of UI tours"""
	completed = {}
	for tour in sparrow.get_all("Form Tour", {"ui_tour": 1}, pluck="name"):
		completed[tour] = {"is_complete": True}

	User = sparrow.qb.DocType("User")
	sparrow.qb.update(User).set("onboarding_status", json.dumps(completed)).run()
