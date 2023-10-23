import sparrow


def execute():
	sparrow.db.delete("DocType", {"name": "Feedback Request"})
