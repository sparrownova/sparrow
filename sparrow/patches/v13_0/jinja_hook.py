# Copyright (c) 2021, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from click import secho

import sparrow


def execute():
	if sparrow.get_hooks("jenv"):
		print()
		secho(
			'WARNING: The hook "jenv" is deprecated. Follow the migration guide to use the new "jinja" hook.',
			fg="yellow",
		)
		secho("https://github.com/sparrownova/sparrow/wiki/Migrating-to-Version-13", fg="yellow")
		print()
