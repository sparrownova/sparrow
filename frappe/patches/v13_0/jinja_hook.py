# Copyright (c) 2021, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

from click import secho

import frappe


def execute():
	if frappe.get_hooks("jenv"):
		print()
		secho(
			'WARNING: The hook "jenv" is deprecated. Follow the migration guide to use the new "jinja" hook.',
			fg="yellow",
		)
		secho("https://github.com/sparrownova/sparrow/wiki/Migrating-to-Version-13", fg="yellow")
		print()
