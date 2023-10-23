# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import sparrow
import sparrow.cache_manager
from sparrow.model import log_types
from sparrow.model.document import Document


class MilestoneTracker(Document):
	def on_update(self):
		sparrow.cache_manager.clear_doctype_map("Milestone Tracker", self.document_type)

	def on_trash(self):
		sparrow.cache_manager.clear_doctype_map("Milestone Tracker", self.document_type)

	def apply(self, doc):
		before_save = doc.get_doc_before_save()
		from_value = before_save and before_save.get(self.track_field) or None
		if from_value != doc.get(self.track_field):
			sparrow.get_doc(
				dict(
					doctype="Milestone",
					reference_type=doc.doctype,
					reference_name=doc.name,
					track_field=self.track_field,
					from_value=from_value,
					value=doc.get(self.track_field),
					milestone_tracker=self.name,
				)
			).insert(ignore_permissions=True)


def evaluate_milestone(doc, event):
	if (
		sparrow.flags.in_install
		or sparrow.flags.in_migrate
		or sparrow.flags.in_setup_wizard
		or doc.doctype in log_types
	):
		return

	# track milestones related to this doctype
	for d in get_milestone_trackers(doc.doctype):
		sparrow.get_doc("Milestone Tracker", d.get("name")).apply(doc)


def get_milestone_trackers(doctype):
	return sparrow.cache_manager.get_doctype_map(
		"Milestone Tracker", doctype, dict(document_type=doctype, disabled=0)
	)
