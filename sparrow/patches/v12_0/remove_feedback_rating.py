import sparrow


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	sparrow.delete_doc("DocType", "Feedback Trigger")
	sparrow.delete_doc("DocType", "Feedback Rating")
