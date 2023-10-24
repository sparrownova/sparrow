# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow.model.document import Document
from sparrow.modules.export_file import export_to_files


class FormTour(Document):
	def before_save(self):
		if self.is_standard and not self.module:
			if self.workspace_name:
				self.module = sparrow.db.get_value("Workspace", self.workspace_name, "module")
			elif self.dashboard_name:
				dashboard_doctype = sparrow.db.get_value("Dashboard", self.dashboard_name, "module")
				self.module = sparrow.db.get_value("DocType", dashboard_doctype, "module")
			else:
				self.module = "Desk"
		if not self.ui_tour:
			meta = sparrow.get_meta(self.reference_doctype)
			for step in self.steps:
				if step.is_table_field and step.parent_fieldname:
					parent_field_df = meta.get_field(step.parent_fieldname)
					step.child_doctype = parent_field_df.options
					field_df = sparrow.get_meta(step.child_doctype).get_field(step.fieldname)
					step.label = field_df.label
					step.fieldtype = field_df.fieldtype
				else:
					field_df = meta.get_field(step.fieldname)
					step.label = field_df.label
					step.fieldtype = field_df.fieldtype

	def on_update(self):
		sparrow.cache().delete_key("bootinfo")

		if sparrow.conf.developer_mode and self.is_standard:
			export_to_files([["Form Tour", self.name]], self.module)

	def on_trash(self):
		sparrow.cache().delete_key("bootinfo")


@sparrow.whitelist()
def reset_tour(tour_name):
	for user in sparrow.get_all("User"):
		user_doc = sparrow.get_doc("User", user.name)
		onboarding_status = sparrow.parse_json(user_doc.onboarding_status)
		onboarding_status.pop(tour_name, None)
		user_doc.onboarding_status = sparrow.as_json(onboarding_status)
		user_doc.save()


@sparrow.whitelist()
def update_user_status(value, step):
	from sparrow.utils.telemetry import capture

	step = sparrow.parse_json(step)
	tour = sparrow.parse_json(value)

	capture(
		sparrow.scrub(f"{step.parent}_{step.title}"),
		app="sparrow_ui_tours",
		properties={"is_completed": tour.is_completed},
	)
	sparrow.db.set_value(
		"User", sparrow.session.user, "onboarding_status", value, update_modified=False
	)

	sparrow.cache().hdel("bootinfo", sparrow.session.user)


def get_onboarding_ui_tours():
	if not sparrow.get_system_settings("enable_onboarding"):
		return []

	ui_tours = sparrow.get_all("Form Tour", filters={"ui_tour": 1}, fields=["page_route", "name"])

	return [[tour.name, json.loads(tour.page_route)] for tour in ui_tours]
