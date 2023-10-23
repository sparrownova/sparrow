# Copyright (c) 2021, Sparrow Technologies and contributors
# For license information, please see license.txt

import os
import subprocess

import sparrow
from sparrow.model.document import Document
from sparrow.modules.export_file import export_doc
from sparrow.query_builder.functions import Max


class PackageRelease(Document):
	def set_version(self):
		# set the next patch release by default
		doctype = sparrow.qb.DocType("Package Release")
		if not self.major:
			self.major = (
                    sparrow.qb.from_(doctype)
                    .where(doctype.package == self.package)
                    .select(Max(doctype.minor))
                    .run()[0][0]
                    or 0
			)

		if not self.minor:
			self.minor = (
                    sparrow.qb.from_(doctype)
                    .where(doctype.package == self.package)
                    .select(Max("minor"))
                    .run()[0][0]
                    or 0
			)
		if not self.patch:
			value = (
                    sparrow.qb.from_(doctype)
                    .where(doctype.package == self.package)
                    .select(Max("patch"))
                    .run()[0][0]
                    or 0
			)
			self.patch = value + 1

	def autoname(self):
		self.set_version()
		self.name = "{}-{}.{}.{}".format(
			sparrow.db.get_value("Package", self.package, "package_name"), self.major, self.minor, self.patch
		)

	def validate(self):
		if self.publish:
			self.export_files()

	def export_files(self):
		"""Export all the documents in this package to site/packages folder"""
		package = sparrow.get_doc("Package", self.package)

		self.export_modules()
		self.export_package_files(package)
		self.make_tarfile(package)

	def export_modules(self):
		for m in sparrow.get_all("Module Def", dict(package=self.package)):
			module = sparrow.get_doc("Module Def", m.name)
			for l in module.meta.links:
				if l.link_doctype == "Module Def":
					continue
				# all documents of the type in the module
				for d in sparrow.get_all(l.link_doctype, dict(module=m.name)):
					export_doc(sparrow.get_doc(l.link_doctype, d.name))

	def export_package_files(self, package):
		# write readme
		with open(sparrow.get_site_path("packages", package.package_name, "README.md"), "w") as readme:
			readme.write(package.readme)

		# write license
		if package.license:
			with open(sparrow.get_site_path("packages", package.package_name, "LICENSE.md"), "w") as license:
				license.write(package.license)

		# write package.json as `frappe_package.json`
		with open(
			sparrow.get_site_path("packages", package.package_name, package.package_name + ".json"), "w"
		) as packagefile:
			packagefile.write(sparrow.as_json(package.as_dict(no_nulls=True)))

	def make_tarfile(self, package):
		# make tarfile
		filename = f"{self.name}.tar.gz"
		subprocess.check_output(
			["tar", "czf", filename, package.package_name], cwd=sparrow.get_site_path("packages")
		)

		# move file
		subprocess.check_output(
			["mv", sparrow.get_site_path("packages", filename), sparrow.get_site_path("public", "files")]
		)

		# make attachment
		file = sparrow.get_doc(
			dict(
				doctype="File",
				file_url="/" + os.path.join("files", filename),
				attached_to_doctype=self.doctype,
				attached_to_name=self.name,
			)
		)

		file.flags.ignore_duplicate_entry_error = True
		file.insert()
