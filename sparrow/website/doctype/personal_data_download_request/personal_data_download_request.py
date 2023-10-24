# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json

import sparrow
from sparrow import _
from sparrow.model.document import Document
from sparrow.utils.verified_command import get_signed_params


class PersonalDataDownloadRequest(Document):
	def after_insert(self):
		personal_data = get_user_data(self.user)

		sparrow.enqueue_doc(
			self.doctype,
			self.name,
			"generate_file_and_send_mail",
			queue="short",
			personal_data=personal_data,
			now=sparrow.flags.in_test,
		)

	def generate_file_and_send_mail(self, personal_data):
		"""generate the file link for download"""
		user_name = self.user_name.replace(" ", "-")
		f = sparrow.get_doc(
			{
				"doctype": "File",
				"file_name": "Personal-Data-" + user_name + "-" + self.name + ".json",
				"attached_to_doctype": "Personal Data Download Request",
				"attached_to_name": self.name,
				"content": str(personal_data),
				"is_private": 1,
			}
		)
		f.save(ignore_permissions=True)

		file_link = (
                sparrow.utils.get_url("/api/method/sparrow.utils.file_manager.download_file")
                + "?"
                + get_signed_params({"file_url": f.file_url})
		)
		host_name = sparrow.local.site
		sparrow.sendmail(
			recipients=self.user,
			subject=_("Download Your Data"),
			template="download_data",
			args={
				"user": self.user,
				"user_name": self.user_name,
				"link": file_link,
				"host_name": host_name,
			},
			header=[_("Download Your Data"), "green"],
		)


def get_user_data(user):
	"""returns user data not linked to User doctype"""
	hooks = sparrow.get_hooks("user_data_fields")
	data = {}
	for hook in hooks:
		d = data.get(hook.get("doctype"), [])
		d += sparrow.get_all(hook.get("doctype"), {hook.get("filter_by", "owner"): user}, ["*"])
		if d:
			data.update({hook.get("doctype"): d})
	return json.dumps(data, indent=2, default=str)