# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.model.document import Document


class InvalidAppOrder(sparrow.ValidationError):
	pass


class InstalledApplications(Document):
	def update_versions(self):
		self.delete_key("installed_applications")
		for app in sparrow.utils.get_installed_apps_info():
			self.append(
				"installed_applications",
				{
					"app_name": app.get("app_name"),
					"app_version": app.get("version") or "UNVERSIONED",
					"git_branch": app.get("branch") or "UNVERSIONED",
				},
			)
		self.save()


@sparrow.whitelist()
def update_installed_apps_order(new_order: list[str] | str):
	"""Change the ordering of `installed_apps` global

	This list is used to resolve hooks and by default it's order of installation on site.

	Sometimes it might not be the ordering you want, so thie function is provided to override it.
	"""
	sparrow.only_for("System Manager")

	if isinstance(new_order, str):
		new_order = json.loads(new_order)

	sparrow.local.request_cache and sparrow.local.request_cache.clear()
	existing_order = sparrow.get_installed_apps(_ensure_on_snova=True)

	if set(existing_order) != set(new_order) or not isinstance(new_order, list):
		sparrow.throw(
			_("You are only allowed to update order, do not remove or add apps."), exc=InvalidAppOrder
		)

	# Ensure sparrow is always first regardless of user's preference.
	if "sparrow" in new_order:
		new_order.remove("sparrow")
	new_order.insert(0, "sparrow")

	sparrow.db.set_global("installed_apps", json.dumps(new_order))

	_create_version_log_for_change(existing_order, new_order)


def _create_version_log_for_change(old, new):
	version = sparrow.new_doc("Version")
	version.ref_doctype = "DefaultValue"
	version.docname = "installed_apps"
	version.data = sparrow.as_json({"changed": [["current", json.dumps(old), json.dumps(new)]]})
	version.flags.ignore_links = True  # This is a fake doctype
	version.flags.ignore_permissions = True
	version.insert()


@sparrow.whitelist()
def get_installed_app_order() -> list[str]:
	sparrow.only_for("System Manager")

	return sparrow.get_installed_apps(_ensure_on_snova=True)
