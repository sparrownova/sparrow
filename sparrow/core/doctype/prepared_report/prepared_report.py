# Copyright (c) 2018, Sparrow Technologies and contributors
# License: MIT. See LICENSE


import json

from rq import get_current_job

import sparrow
from sparrow.desk.form.load import get_attachments
from sparrow.desk.query_report import generate_report_result
from sparrow.model.document import Document
from sparrow.monitor import add_data_to_monitor
from sparrow.utils import gzip_compress, gzip_decompress
from sparrow.utils.background_jobs import enqueue


class PreparedReport(Document):
	@property
	def queued_by(self):
		return self.owner

	@property
	def queued_at(self):
		return self.creation

	@staticmethod
	def clear_old_logs(days=30):
		prepared_reports_to_delete = sparrow.get_all(
			"Prepared Report",
			filters={"modified": ["<", sparrow.utils.add_days(sparrow.utils.now(), -days)]},
		)

		for batch in sparrow.utils.create_batch(prepared_reports_to_delete, 100):
			enqueue(method=delete_prepared_reports, reports=batch)

	def before_insert(self):
		self.status = "Queued"

	def after_insert(self):
		enqueue(
			generate_report,
			queue="long",
			prepared_report=self.name,
			timeout=1500,
			enqueue_after_commit=True,
		)

	def get_prepared_data(self, with_file_name=False):
		if attachments := get_attachments(self.doctype, self.name):
			attachment = attachments[0]
			attached_file = sparrow.get_doc("File", attachment.name)

			if with_file_name:
				return (gzip_decompress(attached_file.get_content()), attachment.file_name)
			return gzip_decompress(attached_file.get_content())


def generate_report(prepared_report):
	update_job_id(prepared_report, get_current_job().id)

	instance = sparrow.get_doc("Prepared Report", prepared_report)
	report = sparrow.get_doc("Report", instance.report_name)

	add_data_to_monitor(report=instance.report_name)

	try:
		report.custom_columns = []

		if report.report_type == "Custom Report":
			custom_report_doc = report
			reference_report = custom_report_doc.reference_report
			report = sparrow.get_doc("Report", reference_report)
			if custom_report_doc.json:
				data = json.loads(custom_report_doc.json)
				if data:
					report.custom_columns = data["columns"]

		result = generate_report_result(report=report, filters=instance.filters, user=instance.owner)
		create_json_gz_file(result, instance.doctype, instance.name)

		instance.status = "Completed"
	except Exception:
		instance.status = "Error"
		instance.error_message = sparrow.get_traceback()

	instance.report_end_time = sparrow.utils.now()
	instance.save(ignore_permissions=True)

	sparrow.publish_realtime(
		"report_generated",
		{"report_name": instance.report_name, "name": instance.name},
		user=sparrow.session.user,
	)


def update_job_id(prepared_report, job_id):
	sparrow.db.set_value("Prepared Report", prepared_report, "job_id", job_id, update_modified=False)
	sparrow.db.commit()


@sparrow.whitelist()
def make_prepared_report(report_name, filters=None):
	"""run reports in background"""
	prepared_report = sparrow.get_doc(
		{
			"doctype": "Prepared Report",
			"report_name": report_name,
			"filters": process_filters_for_prepared_report(filters),
		}
	).insert(ignore_permissions=True)

	return {"name": prepared_report.name}


@sparrow.whitelist()
def get_reports_in_queued_state(report_name, filters):
	reports = sparrow.get_all(
		"Prepared Report",
		filters={
			"report_name": report_name,
			"filters": process_filters_for_prepared_report(filters),
			"status": "Queued",
			"owner": sparrow.session.user,
		},
	)
	return reports


def get_completed_prepared_report(filters, user, report_name):
	return sparrow.db.get_value(
		"Prepared Report",
		filters={
			"status": "Completed",
			"filters": process_filters_for_prepared_report(filters),
			"owner": user,
			"report_name": report_name,
		},
	)


@sparrow.whitelist()
def delete_prepared_reports(reports):
	reports = sparrow.parse_json(reports)
	for report in reports:
		prepared_report = sparrow.get_doc("Prepared Report", report["name"])
		if prepared_report.has_permission():
			prepared_report.delete(ignore_permissions=True, delete_permanently=True)


def process_filters_for_prepared_report(filters):
	if isinstance(filters, str):
		filters = json.loads(filters)

	# This looks like an insanity but, without this it'd be very hard to find Prepared Reports matching given condition
	# We're ensuring that spacing is consistent. e.g. JS seems to put no spaces after ":", Python on the other hand does.
	# We are also ensuring that order of keys is same so generated JSON string will be identical too.
	# PS: sparrow.as_json sorts keys
	return sparrow.as_json(filters, indent=None, separators=(",", ":"))


def create_json_gz_file(data, dt, dn):
	# Storing data in CSV file causes information loss
	# Reports like P&L Statement were completely unsuable because of this
	json_filename = "{}.json.gz".format(
		sparrow.utils.data.format_datetime(sparrow.utils.now(), "Y-m-d-H:M")
	)
	encoded_content = sparrow.safe_encode(sparrow.as_json(data))
	compressed_content = gzip_compress(encoded_content)

	# Call save() file function to upload and attach the file
	_file = sparrow.get_doc(
		{
			"doctype": "File",
			"file_name": json_filename,
			"attached_to_doctype": dt,
			"attached_to_name": dn,
			"content": compressed_content,
			"is_private": 1,
		}
	)
	_file.save(ignore_permissions=True)


@sparrow.whitelist()
def download_attachment(dn):
	pr = sparrow.get_doc("Prepared Report", dn)
	if not pr.has_permission("read"):
		sparrow.throw(sparrow._("Cannot Download Report due to insufficient permissions"))

	data, file_name = pr.get_prepared_data(with_file_name=True)
	sparrow.local.response.filename = file_name[:-3]
	sparrow.local.response.filecontent = data
	sparrow.local.response.type = "binary"


def get_permission_query_condition(user):
	if not user:
		user = sparrow.session.user
	if user == "Administrator":
		return None

	from sparrow.utils.user import UserPermissions

	user = UserPermissions(user)

	if "System Manager" in user.roles:
		return None

	reports = [sparrow.db.escape(report) for report in user.get_all_reports().keys()]

	return """`tabPrepared Report`.report_name in ({reports})""".format(reports=",".join(reports))


def has_permission(doc, user):
	if not user:
		user = sparrow.session.user
	if user == "Administrator":
		return True

	from sparrow.utils.user import UserPermissions

	user = UserPermissions(user)

	if "System Manager" in user.roles:
		return True

	return doc.report_name in user.get_all_reports().keys()
