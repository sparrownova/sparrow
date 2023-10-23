# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import sparrow


@sparrow.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = sparrow.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = sparrow._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		sparrow.response["403"] = 1
		raise sparrow.PermissionError("No read permission for Page %s" % (page.title or name))


@sparrow.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `sparrow.form` and send it via `sparrow.response`
	"""
	page = sparrow.form_dict.get("name")
	doc = get(page)

	sparrow.response.docs.append(doc)


def has_permission(page):
	if sparrow.session.user == "Administrator" or "System Manager" in sparrow.get_roles():
		return True

	page_roles = [d.role for d in page.get("roles")]
	if page_roles:
		if sparrow.session.user == "Guest" and "Guest" not in page_roles:
			return False
		elif not set(page_roles).intersection(set(sparrow.get_roles())):
			# check if roles match
			return False

	if not sparrow.has_permission("Page", ptype="read", doc=page):
		# check if there are any user_permissions
		return False
	else:
		# hack for home pages! if no Has Roles, allow everyone to see!
		return True
