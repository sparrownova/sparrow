import sparrow


def execute():
	providers = sparrow.get_all("Social Login Key")

	for provider in providers:
		doc = sparrow.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
