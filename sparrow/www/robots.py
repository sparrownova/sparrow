import sparrow

base_template_path = "www/robots.txt"


def get_context(context):
	robots_txt = (
		sparrow.db.get_single_value("Website Settings", "robots_txt")
		or (sparrow.local.conf.robots_txt and sparrow.read_file(sparrow.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}
