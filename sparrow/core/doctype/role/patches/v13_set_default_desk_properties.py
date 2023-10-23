import sparrow

from ..role import desk_properties


def execute():
	for role in sparrow.get_all("Role", ["name", "desk_access"]):
		role_doc = sparrow.get_doc("Role", role.name)
		for key in desk_properties:
			role_doc.set(key, role_doc.desk_access)
		role_doc.save()
