# Copyright (c) 2022, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.deferred_insert import deferred_insert as _deferred_insert
from sparrow.model.document import Document


class RouteHistory(Document):
	@staticmethod
	def clear_old_logs(days=30):
		from sparrow.query_builder import Interval
		from sparrow.query_builder.functions import Now

		table = sparrow.qb.DocType("Route History")
		sparrow.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@sparrow.whitelist()
def deferred_insert(routes):
	routes = [
		{
			"user": sparrow.session.user,
			"route": route.get("route"),
			"creation": route.get("creation"),
		}
		for route in sparrow.parse_json(routes)
	]

	_deferred_insert("Route History", routes)


@sparrow.whitelist()
def frequently_visited_links():
	return sparrow.get_all(
		"Route History",
		fields=["route", "count(name) as count"],
		filters={"user": sparrow.session.user},
		group_by="route",
		order_by="count desc",
		limit=5,
	)
