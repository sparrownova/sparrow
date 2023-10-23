import sparrow


def execute():
	sparrow.delete_doc_if_exists("DocType", "Web View")
	sparrow.delete_doc_if_exists("DocType", "Web View Component")
	sparrow.delete_doc_if_exists("DocType", "CSS Class")
