# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow

# import sparrow
from sparrow.model.document import Document


class DashboardSettings(Document):
	pass


@sparrow.whitelist()
def create_dashboard_settings(user):
	if not sparrow.db.exists("Dashboard Settings", user):
		doc = sparrow.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		sparrow.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = sparrow.session.user

	return f"""(`tabDashboard Settings`.name = {sparrow.db.escape(user)})"""


@sparrow.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = sparrow.parse_json(reset)
	doc = sparrow.get_doc("Dashboard Settings", sparrow.session.user)
	chart_config = sparrow.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = sparrow.parse_json(config)
		if not chart_name in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	sparrow.db.set_value(
		"Dashboard Settings", sparrow.session.user, "chart_config", json.dumps(chart_config)
	)
