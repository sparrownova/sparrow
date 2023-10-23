# Copyright (c) 2019, Sparrow Technologies and Contributors
# License: MIT. See LICENSE
import sparrow
import sparrow.cache_manager
from sparrow.tests.utils import SparrowTestCase


class TestMilestoneTracker(SparrowTestCase):
	def test_milestone(self):
		sparrow.db.delete("Milestone Tracker")

		sparrow.cache().delete_key("milestone_tracker_map")

		milestone_tracker = sparrow.get_doc(
			dict(doctype="Milestone Tracker", document_type="ToDo", track_field="status")
		).insert()

		todo = sparrow.get_doc(dict(doctype="ToDo", description="test milestone", status="Open")).insert()

		milestones = sparrow.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
		)

		self.assertEqual(len(milestones), 1)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Open")

		todo.status = "Closed"
		todo.save()

		milestones = sparrow.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
			order_by="modified desc",
		)

		self.assertEqual(len(milestones), 2)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Closed")

		# cleanup
		sparrow.db.delete("Milestone")
		milestone_tracker.delete()
