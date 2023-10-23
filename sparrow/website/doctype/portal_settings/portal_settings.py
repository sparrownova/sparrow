# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow.model.document import Document


class PortalSettings(Document):
	def add_item(self, item):
		"""insert new portal menu item if route is not set, or role is different"""
		exists = [d for d in self.get("menu", []) if d.get("route") == item.get("route")]
		if exists and item.get("role"):
			if exists[0].role != item.get("role"):
				exists[0].role = item.get("role")
				return True
		elif not exists:
			item["enabled"] = 1
			self.append("menu", item)
			return True

	@sparrow.whitelist()
	def reset(self):
		"""Restore defaults"""
		self.menu = []
		self.sync_menu()

	def sync_menu(self):
		"""Sync portal menu items"""
		dirty = False
		for item in sparrow.get_hooks("standard_portal_menu_items"):
			if item.get("role") and not sparrow.db.exists("Role", item.get("role")):
				sparrow.get_doc({"doctype": "Role", "role_name": item.get("role"), "desk_access": 0}).insert()
			if self.add_item(item):
				dirty = True

		if dirty:
			self.remove_deleted_doctype_items()
			self.save()

	def on_update(self):
		self.clear_cache()

	def clear_cache(self):
		# make js and css
		# clear web cache (for menus!)
		sparrow.clear_cache(user="Guest")

		from sparrow.website.utils import clear_cache

		clear_cache()

		# clears role based home pages
		sparrow.clear_cache()

	def remove_deleted_doctype_items(self):
		existing_doctypes = set(sparrow.get_list("DocType", pluck="name"))
		for menu_item in list(self.get("menu")):
			if menu_item.reference_doctype not in existing_doctypes:
				self.remove(menu_item)
