# Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow.model.document import Document
from sparrow.utils.jinja import validate_template


class EmailTemplate(Document):
	@property
	def response_(self):
		return self.response_html if self.use_html else self.response

	def validate(self):
		validate_template(self.subject)
		validate_template(self.response_)

	def get_formatted_subject(self, doc):
		return sparrow.render_template(self.subject, doc)

	def get_formatted_response(self, doc):
		return sparrow.render_template(self.response_, doc)

	def get_formatted_email(self, doc):
		if isinstance(doc, str):
			doc = json.loads(doc)

		return {
			"subject": self.get_formatted_subject(doc),
			"message": self.get_formatted_response(doc),
		}


@sparrow.whitelist()
def get_email_template(template_name, doc):
	"""Returns the processed HTML of a email template with the given doc"""

	email_template = sparrow.get_doc("Email Template", template_name)
	return email_template.get_formatted_email(doc)
