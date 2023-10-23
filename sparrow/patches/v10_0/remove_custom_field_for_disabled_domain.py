import sparrow


def execute():
	sparrow.reload_doc("core", "doctype", "domain")
	sparrow.reload_doc("core", "doctype", "has_domain")
	active_domains = sparrow.get_active_domains()
	all_domains = sparrow.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = sparrow.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
