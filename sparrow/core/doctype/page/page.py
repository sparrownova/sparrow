# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import os

import sparrow
from sparrow import _, conf, safe_decode
from sparrow.build import html_to_js_template
from sparrow.core.doctype.custom_role.custom_role import get_custom_allowed_roles
from sparrow.desk.form.meta import get_code_files_via_hooks, get_js
from sparrow.desk.utils import validate_route_conflict
from sparrow.model.document import Document
from sparrow.model.utils import render_include


class Page(Document):
	def autoname(self):
		"""
		Creates a url friendly name for this page.
		Will restrict the name to 30 characters, if there exists a similar name,
		it will add name-1, name-2 etc.
		"""
		from sparrow.utils import cint

		if (self.name and self.name.startswith("New Page")) or not self.name:
			self.name = self.page_name.lower().replace('"', "").replace("'", "").replace(" ", "-")[:20]
			if sparrow.db.exists("Page", self.name):
				cnt = sparrow.db.sql(
					"""select name from tabPage
					where name like "%s-%%" order by name desc limit 1"""
					% self.name
				)
				if cnt:
					cnt = cint(cnt[0][0].split("-")[-1]) + 1
				else:
					cnt = 1
				self.name += "-" + str(cnt)

	def validate(self):
		validate_route_conflict(self.doctype, self.name)

		if self.is_new() and not getattr(conf, "developer_mode", 0):
			sparrow.throw(_("Not in Developer Mode"))

		# setting ignore_permissions via update_setup_wizard_access (setup_wizard.py)
		if sparrow.session.user != "Administrator" and not self.flags.ignore_permissions:
			sparrow.throw(_("Only Administrator can edit"))

	# export
	def on_update(self):
		"""
		Writes the .json for this page and if write_content is checked,
		it will write out a .html file
		"""
		if self.flags.do_not_update_json:
			return

		from sparrow.core.doctype.doctype.doctype import make_module_and_roles

		make_module_and_roles(self, "roles")

		from sparrow.modules.utils import export_module_json

		path = export_module_json(self, self.standard == "Yes", self.module)

		if path:
			# js
			if not os.path.exists(path + ".js"):
				with open(path + ".js", "w") as f:
					f.write(
						"""sparrow.pages['%s'].on_page_load = function(wrapper) {
	var page = sparrow.ui.make_app_page({
		parent: wrapper,
		title: '%s',
		single_column: true
	});
}"""
						% (self.name, self.title)
					)

	def as_dict(self, no_nulls=False):
		d = super().as_dict(no_nulls=no_nulls)
		for key in ("script", "style", "content"):
			d[key] = self.get(key)
		return d

	def on_trash(self):
		delete_custom_role("page", self.name)

	def is_permitted(self):
		"""Returns true if Has Role is not set or the user is allowed."""
		from sparrow.utils import has_common

		allowed = [
			d.role for d in sparrow.get_all("Has Role", fields=["role"], filters={"parent": self.name})
		]

		custom_roles = get_custom_allowed_roles("page", self.name)
		allowed.extend(custom_roles)

		if not allowed:
			return True

		roles = sparrow.get_roles()

		if has_common(roles, allowed):
			return True

	def load_assets(self):
		import os

		from sparrow.modules import get_module_path, scrub

		self.script = ""

		page_name = scrub(self.name)

		path = os.path.join(get_module_path(self.module), "page", page_name)

		# script
		fpath = os.path.join(path, page_name + ".js")
		if os.path.exists(fpath):
			with open(fpath) as f:
				self.script = render_include(f.read())
				self.script += f"\n\n//# sourceURL={page_name}.js"

		# css
		fpath = os.path.join(path, page_name + ".css")
		if os.path.exists(fpath):
			with open(fpath) as f:
				self.style = safe_decode(f.read())

		# html as js template
		for fname in os.listdir(path):
			if fname.endswith(".html"):
				with open(os.path.join(path, fname)) as f:
					template = f.read()
					if "<!-- jinja -->" in template:
						context = sparrow._dict({})
						try:
							out = sparrow.get_attr(
								"{app}.{module}.page.{page}.{page}.get_context".format(
									app=sparrow.local.module_app[scrub(self.module)], module=scrub(self.module), page=page_name
								)
							)(context)

							if out:
								context = out
						except (AttributeError, ImportError):
							pass

						template = sparrow.render_template(template, context)
					self.script = html_to_js_template(fname, template) + self.script

					# flag for not caching this page
					self._dynamic_page = True

		if sparrow.lang != "en":
			from sparrow.translate import get_lang_js

			self.script += get_lang_js("page", self.name)

		for path in get_code_files_via_hooks("page_js", self.name):
			js = get_js(path)
			if js:
				self.script += "\n\n" + js


def delete_custom_role(field, docname):
	name = sparrow.db.get_value("Custom Role", {field: docname}, "name")
	if name:
		sparrow.delete_doc("Custom Role", name)
