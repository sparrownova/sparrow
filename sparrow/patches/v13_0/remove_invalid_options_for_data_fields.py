# Copyright (c) 2022, Sparrow and Contributors
# License: MIT. See LICENSE


import sparrow
from sparrow.model import data_field_options


def execute():
	custom_field = sparrow.qb.DocType("Custom Field")
	(
		sparrow.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
