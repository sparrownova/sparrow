# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document

desk_properties = (
	"search_bar",
	"notifications",
	"list_sidebar",
	"bulk_actions",
	"view_switcher",
	"form_sidebar",
	"timeline",
	"dashboard",
)

STANDARD_ROLES = ("Administrator", "System Manager", "Script Manager", "All", "Guest")


class Role(Document):
	def before_rename(self, old, new, merge=False):
		if old in STANDARD_ROLES:
			sparrow.throw(sparrow._("Standard roles cannot be renamed"))

	def after_insert(self):
		sparrow.cache().hdel("roles", "Administrator")

	def validate(self):
		if self.disabled:
			self.disable_role()
		else:
			self.set_desk_properties()

	def disable_role(self):
		if self.name in STANDARD_ROLES:
			sparrow.throw(sparrow._("Standard roles cannot be disabled"))
		else:
			self.remove_roles()

	def set_desk_properties(self):
		# set if desk_access is not allowed, unset all desk properties
		if self.name == "Guest":
			self.desk_access = 0

		if not self.desk_access:
			for key in desk_properties:
				self.set(key, 0)

	def remove_roles(self):
		sparrow.db.delete("Has Role", {"role": self.name})
		sparrow.clear_cache()

	def on_update(self):
		"""update system user desk access if this has changed in this update"""
		if sparrow.flags.in_install:
			return
		if self.has_value_changed("desk_access"):
			for user_name in get_users(self.name):
				user = sparrow.get_doc("User", user_name)
				user_type = user.user_type
				user.set_system_user()
				if user_type != user.user_type:
					user.save()


def get_info_based_on_role(role, field="email", ignore_permissions=False):
	"""Get information of all users that have been assigned this role"""
	users = sparrow.get_list(
		"Has Role",
		filters={"role": role, "parenttype": "User"},
		parent_doctype="User",
		fields=["parent as user_name"],
		ignore_permissions=ignore_permissions,
	)

	return get_user_info(users, field)


def get_user_info(users, field="email"):
	"""Fetch details about users for the specified field"""
	info_list = []
	for user in users:
		user_info, enabled = sparrow.db.get_value("User", user.get("user_name"), [field, "enabled"])
		if enabled and user_info not in ["admin@example.com", "guest@example.com"]:
			info_list.append(user_info)
	return info_list


def get_users(role):
	return [
		d.parent
		for d in sparrow.get_all(
			"Has Role", filters={"role": role, "parenttype": "User"}, fields=["parent"]
		)
	]


# searches for active employees
@sparrow.whitelist()
@sparrow.validate_and_sanitize_search_inputs
def role_query(doctype, txt, searchfield, start, page_len, filters):
	report_filters = [["Role", "name", "like", f"%{txt}%"], ["Role", "is_custom", "=", 0]]
	if filters and isinstance(filters, list):
		report_filters.extend(filters)

	return sparrow.get_all(
		"Role", limit_start=start, limit_page_length=page_len, filters=report_filters, as_list=1
	)
