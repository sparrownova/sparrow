# Copyright (c) 2020, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.model.document import Document


class OnboardingStep(Document):
	def before_export(self, doc):
		doc.is_complete = 0
		doc.is_skipped = 0


@sparrow.whitelist()
def get_onboarding_steps(ob_steps):
	steps = []
	for s in json.loads(ob_steps):
		doc = sparrow.get_doc("Onboarding Step", s.get("step"))
		step = doc.as_dict().copy()
		step.label = _(doc.title)
		if step.action == "Create Entry":
			step.is_submittable = sparrow.db.get_value(
				"DocType", step.reference_document, "is_submittable", cache=True
			)
		steps.append(step)

	return steps
