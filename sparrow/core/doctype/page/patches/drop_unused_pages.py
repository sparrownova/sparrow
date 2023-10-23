import sparrow


def execute():
	for name in ("desktop", "space"):
		sparrow.delete_doc("Page", name)
