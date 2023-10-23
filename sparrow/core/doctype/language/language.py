# Copyright (c) 2015, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import json
import re

import sparrow
from sparrow import _
from sparrow.model.document import Document


class Language(Document):
	def validate(self):
		validate_with_regex(self.language_code, "Language Code")

	def before_rename(self, old, new, merge=False):
		validate_with_regex(new, "Name")

	def on_update(self):
		sparrow.cache().delete_value("languages_with_name")
		sparrow.cache().delete_value("languages")


def validate_with_regex(name, label):
	pattern = re.compile("^[a-zA-Z]+[-_]*[a-zA-Z]+$")
	if not pattern.match(name):
		sparrow.throw(
			_(
				"""{0} must begin and end with a letter and can only contain letters,
				hyphen or underscore."""
			).format(label)
		)


def export_languages_json():
	"""Export list of all languages"""
	languages = sparrow.get_all("Language", fields=["name", "language_name"])
	languages = [{"name": d.language_name, "code": d.name} for d in languages]

	languages.sort(key=lambda a: a["code"])

	with open(sparrow.get_app_path("sparrow", "geo", "languages.json"), "w") as f:
		f.write(sparrow.as_json(languages))


def sync_languages():
	"""Sync sparrow/geo/languages.json with Language"""
	with open(sparrow.get_app_path("sparrow", "geo", "languages.json")) as f:
		data = json.loads(f.read())

	for l in data:
		if not sparrow.db.exists("Language", l["code"]):
			sparrow.get_doc(
				{
					"doctype": "Language",
					"language_code": l["code"],
					"language_name": l["name"],
					"enabled": 1,
				}
			).insert()


def update_language_names():
	"""Update sparrow/geo/languages.json names (for use via patch)"""
	with open(sparrow.get_app_path("sparrow", "geo", "languages.json")) as f:
		data = json.loads(f.read())

	for l in data:
		sparrow.db.set_value("Language", l["code"], "language_name", l["name"])
