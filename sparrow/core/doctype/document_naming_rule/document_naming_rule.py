# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
from sparrow import _
from sparrow.model.document import Document
from sparrow.model.naming import parse_naming_series
from sparrow.utils.data import evaluate_filters


class DocumentNamingRule(Document):
	def validate(self):
		self.validate_fields_in_conditions()

	def clear_doctype_map(self):
		sparrow.cache_manager.clear_doctype_map(self.doctype, self.document_type)

	def on_update(self):
		self.clear_doctype_map()

	def on_trash(self):
		self.clear_doctype_map()

	def validate_fields_in_conditions(self):
		if self.has_value_changed("document_type"):
			docfields = [x.fieldname for x in sparrow.get_meta(self.document_type).fields]
			for condition in self.conditions:
				if condition.field not in docfields:
					sparrow.throw(
						_("{0} is not a field of doctype {1}").format(
							sparrow.bold(condition.field), sparrow.bold(self.document_type)
						)
					)

	def apply(self, doc):
		"""
		Apply naming rules for the given document. Will set `name` if the rule is matched.
		"""
		if self.conditions:
			if not evaluate_filters(
				doc, [(self.document_type, d.field, d.condition, d.value) for d in self.conditions]
			):
				return

		counter = sparrow.db.get_value(self.doctype, self.name, "counter", for_update=True) or 0
		naming_series = parse_naming_series(self.prefix, doc=doc)

		doc.name = naming_series + ("%0" + str(self.prefix_digits) + "d") % (counter + 1)
		sparrow.db.set_value(self.doctype, self.name, "counter", counter + 1)
