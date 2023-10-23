# Copyright (c) 2022, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model import is_default_field
from sparrow.query_builder import Order
from sparrow.query_builder.functions import Count
from sparrow.query_builder.terms import SubQuery
from sparrow.query_builder.utils import DocType


@sparrow.whitelist()
def get_list_settings(doctype):
	try:
		return sparrow.get_cached_doc("List View Settings", doctype)
	except sparrow.DoesNotExistError:
		sparrow.clear_messages()


@sparrow.whitelist()
def set_list_settings(doctype, values):
	try:
		doc = sparrow.get_doc("List View Settings", doctype)
	except sparrow.DoesNotExistError:
		doc = sparrow.new_doc("List View Settings")
		doc.name = doctype
		sparrow.clear_messages()
	doc.update(sparrow.parse_json(values))
	doc.save()


@sparrow.whitelist()
def get_group_by_count(doctype: str, current_filters: str, field: str) -> list[dict]:
	current_filters = sparrow.parse_json(current_filters)

	if field == "assigned_to":
		ToDo = DocType("ToDo")
		User = DocType("User")
		count = Count("*").as_("count")
		filtered_records = sparrow.qb.get_query(
			doctype,
			filters=current_filters,
			fields=["name"],
			validate_filters=True,
		)

		return (
			sparrow.qb.from_(ToDo)
			.from_(User)
			.select(ToDo.allocated_to.as_("name"), count)
			.where(
				(ToDo.status != "Cancelled")
				& (ToDo.allocated_to == User.name)
				& (User.user_type == "System User")
				& (ToDo.reference_name.isin(SubQuery(filtered_records)))
			)
			.groupby(ToDo.allocated_to)
			.orderby(count, order=Order.desc)
			.limit(50)
			.run(as_dict=True)
		)

	if not sparrow.get_meta(doctype).has_field(field) and not is_default_field(field):
		raise ValueError("Field does not belong to doctype")

	return sparrow.get_list(
		doctype,
		filters=current_filters,
		group_by=f"`tab{doctype}`.{field}",
		fields=["count(*) as count", f"`{field}` as name"],
		order_by="count desc",
		limit=50,
	)
