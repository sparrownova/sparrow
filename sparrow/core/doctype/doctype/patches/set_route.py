import sparrow
from sparrow.desk.utils import slug


def execute():
	for doctype in sparrow.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			sparrow.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
