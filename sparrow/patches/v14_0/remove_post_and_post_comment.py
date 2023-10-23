import sparrow


def execute():
	sparrow.delete_doc_if_exists("DocType", "Post")
	sparrow.delete_doc_if_exists("DocType", "Post Comment")
