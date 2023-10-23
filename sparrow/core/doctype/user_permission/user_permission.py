# Copyright (c) 2021, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.core.utils import find
from sparrow.desk.form.linked_with import get_linked_doctypes
from sparrow.model.document import Document
from sparrow.utils import cstr


class UserPermission(Document):
	def validate(self):
		self.validate_user_permission()
		self.validate_default_permission()

	def on_update(self):
		sparrow.cache().hdel("user_permissions", self.user)
		sparrow.publish_realtime("update_user_permissions", user=self.user, after_commit=True)

	def on_trash(self):
		sparrow.cache().hdel("user_permissions", self.user)
		sparrow.publish_realtime("update_user_permissions", user=self.user, after_commit=True)

	def validate_user_permission(self):
		"""checks for duplicate user permission records"""

		duplicate_exists = sparrow.get_all(
			self.doctype,
			filters={
				"allow": self.allow,
				"for_value": self.for_value,
				"user": self.user,
				"applicable_for": cstr(self.applicable_for),
				"apply_to_all_doctypes": self.apply_to_all_doctypes,
				"name": ["!=", self.name],
			},
			limit=1,
		)
		if duplicate_exists:
			sparrow.throw(_("User permission already exists"), sparrow.DuplicateEntryError)

	def validate_default_permission(self):
		"""validate user permission overlap for default value of a particular doctype"""
		overlap_exists = []
		if self.is_default:
			overlap_exists = sparrow.get_all(
				self.doctype,
				filters={"allow": self.allow, "user": self.user, "is_default": 1, "name": ["!=", self.name]},
				or_filters={
					"applicable_for": cstr(self.applicable_for),
					"apply_to_all_doctypes": 1,
				},
				limit=1,
			)
		if overlap_exists:
			ref_link = sparrow.get_desk_link(self.doctype, overlap_exists[0].name)
			sparrow.throw(_("{0} has already assigned default value for {1}.").format(ref_link, self.allow))


def send_user_permissions(bootinfo):
	bootinfo.user["user_permissions"] = get_user_permissions()


@sparrow.whitelist()
def get_user_permissions(user=None):
	"""Get all users permissions for the user as a dict of doctype"""
	# if this is called from client-side,
	# user can access only his/her user permissions
	if sparrow.request and sparrow.local.form_dict.cmd == "get_user_permissions":
		user = sparrow.session.user

	if not user:
		user = sparrow.session.user

	if not user or user in ("Administrator", "Guest"):
		return {}

	cached_user_permissions = sparrow.cache().hget("user_permissions", user)

	if cached_user_permissions is not None:
		return cached_user_permissions

	out = {}

	def add_doc_to_perm(perm, doc_name, is_default):
		# group rules for each type
		# for example if allow is "Customer", then build all allowed customers
		# in a list
		if not out.get(perm.allow):
			out[perm.allow] = []

		out[perm.allow].append(
			sparrow._dict(
				{"doc": doc_name, "applicable_for": perm.get("applicable_for"), "is_default": is_default}
			)
		)

	try:
		for perm in sparrow.get_all(
			"User Permission",
			fields=["allow", "for_value", "applicable_for", "is_default", "hide_descendants"],
			filters=dict(user=user),
		):

			meta = sparrow.get_meta(perm.allow)
			add_doc_to_perm(perm, perm.for_value, perm.is_default)

			if meta.is_nested_set() and not perm.hide_descendants:
				decendants = sparrow.db.get_descendants(perm.allow, perm.for_value)
				for doc in decendants:
					add_doc_to_perm(perm, doc, False)

		out = sparrow._dict(out)
		sparrow.cache().hset("user_permissions", user, out)
	except sparrow.db.SQLError as e:
		if sparrow.db.is_table_missing(e):
			# called from patch
			pass

	return out


def user_permission_exists(user, allow, for_value, applicable_for=None):
	"""Checks if similar user permission already exists"""
	user_permissions = get_user_permissions(user).get(allow, [])
	if not user_permissions:
		return None
	has_same_user_permission = find(
		user_permissions,
		lambda perm: perm["doc"] == for_value and perm.get("applicable_for") == applicable_for,
	)

	return has_same_user_permission


@sparrow.whitelist()
@sparrow.validate_and_sanitize_search_inputs
def get_applicable_for_doctype_list(doctype, txt, searchfield, start, page_len, filters):
	linked_doctypes_map = get_linked_doctypes(doctype, True)

	linked_doctypes = []
	for linked_doctype, linked_doctype_values in linked_doctypes_map.items():
		linked_doctypes.append(linked_doctype)
		child_doctype = linked_doctype_values.get("child_doctype")
		if child_doctype:
			linked_doctypes.append(child_doctype)

	linked_doctypes += [doctype]

	if txt:
		linked_doctypes = [d for d in linked_doctypes if txt.lower() in d.lower()]

	linked_doctypes.sort()

	return_list = []
	for doctype in linked_doctypes[start:page_len]:
		return_list.append([doctype])

	return return_list


def get_permitted_documents(doctype):
	"""Returns permitted documents from the given doctype for the session user"""
	# sort permissions in a way to make the first permission in the list to be default
	user_perm_list = sorted(
		get_user_permissions().get(doctype, []), key=lambda x: x.get("is_default"), reverse=True
	)

	return [d.get("doc") for d in user_perm_list if d.get("doc")]


@sparrow.whitelist()
def check_applicable_doc_perm(user, doctype, docname):
	sparrow.only_for("System Manager")
	applicable = []
	doc_exists = sparrow.get_all(
		"User Permission",
		fields=["name"],
		filters={
			"user": user,
			"allow": doctype,
			"for_value": docname,
			"apply_to_all_doctypes": 1,
		},
		limit=1,
	)
	if doc_exists:
		applicable = get_linked_doctypes(doctype).keys()
	else:
		data = sparrow.get_all(
			"User Permission",
			fields=["applicable_for"],
			filters={
				"user": user,
				"allow": doctype,
				"for_value": docname,
			},
		)
		for permission in data:
			applicable.append(permission.applicable_for)
	return applicable


@sparrow.whitelist()
def clear_user_permissions(user, for_doctype):
	sparrow.only_for("System Manager")
	total = sparrow.db.count("User Permission", {"user": user, "allow": for_doctype})

	if total:
		sparrow.db.delete(
			"User Permission",
			{
				"allow": for_doctype,
				"user": user,
			},
		)
		sparrow.clear_cache()

	return total


@sparrow.whitelist()
def add_user_permissions(data):
	"""Add and update the user permissions"""
	sparrow.only_for("System Manager")
	if isinstance(data, str):
		data = json.loads(data)
	data = sparrow._dict(data)

	# get all doctypes on whom this permission is applied
	perm_applied_docs = check_applicable_doc_perm(data.user, data.doctype, data.docname)
	exists = sparrow.db.exists(
		"User Permission",
		{
			"user": data.user,
			"allow": data.doctype,
			"for_value": data.docname,
			"apply_to_all_doctypes": 1,
		},
	)
	if data.apply_to_all_doctypes == 1 and not exists:
		remove_applicable(perm_applied_docs, data.user, data.doctype, data.docname)
		insert_user_perm(
			data.user, data.doctype, data.docname, data.is_default, data.hide_descendants, apply_to_all=1
		)
		return 1
	elif len(data.applicable_doctypes) > 0 and data.apply_to_all_doctypes != 1:
		remove_apply_to_all(data.user, data.doctype, data.docname)
		update_applicable(
			perm_applied_docs, data.applicable_doctypes, data.user, data.doctype, data.docname
		)
		for applicable in data.applicable_doctypes:
			if applicable not in perm_applied_docs:
				insert_user_perm(
					data.user,
					data.doctype,
					data.docname,
					data.is_default,
					data.hide_descendants,
					applicable=applicable,
				)
			elif exists:
				insert_user_perm(
					data.user,
					data.doctype,
					data.docname,
					data.is_default,
					data.hide_descendants,
					applicable=applicable,
				)
		return 1
	return 0


def insert_user_perm(
	user, doctype, docname, is_default=0, hide_descendants=0, apply_to_all=None, applicable=None
):
	user_perm = sparrow.new_doc("User Permission")
	user_perm.user = user
	user_perm.allow = doctype
	user_perm.for_value = docname
	user_perm.is_default = is_default
	user_perm.hide_descendants = hide_descendants
	if applicable:
		user_perm.applicable_for = applicable
		user_perm.apply_to_all_doctypes = 0
	else:
		user_perm.apply_to_all_doctypes = 1
	user_perm.insert()


def remove_applicable(perm_applied_docs, user, doctype, docname):
	for applicable_for in perm_applied_docs:
		sparrow.db.delete(
			"User Permission",
			{
				"applicable_for": applicable_for,
				"for_value": docname,
				"allow": doctype,
				"user": user,
			},
		)


def remove_apply_to_all(user, doctype, docname):
	sparrow.db.delete(
		"User Permission",
		{
			"apply_to_all_doctypes": 1,
			"for_value": docname,
			"allow": doctype,
			"user": user,
		},
	)


def update_applicable(already_applied, to_apply, user, doctype, docname):
	for applied in already_applied:
		if applied not in to_apply:
			sparrow.db.delete(
				"User Permission",
				{
					"applicable_for": applied,
					"for_value": docname,
					"allow": doctype,
					"user": user,
				},
			)
