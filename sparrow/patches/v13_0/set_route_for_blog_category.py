import sparrow


def execute():
	categories = sparrow.get_list("Blog Category")
	for category in categories:
		doc = sparrow.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
