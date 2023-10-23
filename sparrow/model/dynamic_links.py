# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

import sparrow

# select doctypes that are accessed by the user (not read_only) first, so that the
# the validation message shows the user-facing doctype first.
# For example Journal Entry should be validated before GL Entry (which is an internal doctype)

dynamic_link_queries = [
	"""select `tabDocField`.parent,
		`tabDocType`.read_only, `tabDocType`.in_create,
		`tabDocField`.fieldname, `tabDocField`.options
	from `tabDocField`, `tabDocType`
	where `tabDocField`.fieldtype='Dynamic Link' and
	`tabDocType`.`name`=`tabDocField`.parent
	order by `tabDocType`.read_only, `tabDocType`.in_create""",
	"""select `tabCustom Field`.dt as parent,
		`tabDocType`.read_only, `tabDocType`.in_create,
		`tabCustom Field`.fieldname, `tabCustom Field`.options
	from `tabCustom Field`, `tabDocType`
	where `tabCustom Field`.fieldtype='Dynamic Link' and
	`tabDocType`.`name`=`tabCustom Field`.dt
	order by `tabDocType`.read_only, `tabDocType`.in_create""",
]


def get_dynamic_link_map(for_delete=False):
	"""Build a map of all dynamically linked tables. For example,
	        if Note is dynamically linked to ToDo, the function will return
	        `{"Note": ["ToDo"], "Sales Invoice": ["Journal Entry Detail"]}`

	Note: Will not map single doctypes
	"""
	if getattr(sparrow.local, "dynamic_link_map", None) is None or sparrow.flags.in_test:
		# Build from scratch
		dynamic_link_map = {}
		for df in get_dynamic_links():
			meta = sparrow.get_meta(df.parent)
			if meta.issingle:
				# always check in Single DocTypes
				dynamic_link_map.setdefault(meta.name, []).append(df)
			else:
				try:
					links = sparrow.db.sql_list("""select distinct {options} from `tab{parent}`""".format(**df))
					for doctype in links:
						dynamic_link_map.setdefault(doctype, []).append(df)
				except sparrow.db.TableMissingError:  # noqa: E722
					pass

		sparrow.local.dynamic_link_map = dynamic_link_map
	return sparrow.local.dynamic_link_map


def get_dynamic_links():
	"""Return list of dynamic link fields as DocField.
	Uses cache if possible"""
	df = []
	for query in dynamic_link_queries:
		df += sparrow.db.sql(query, as_dict=True)
	return df
