# Copyright (c) 2021, Sparrow Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE
"""
	sparrow.coverage
	~~~~~~~~~~~~~~~~

	Coverage settings for sparrow
"""

STANDARD_INCLUSIONS = ["*.py"]

STANDARD_EXCLUSIONS = [
	"*.js",
	"*.xml",
	"*.pyc",
	"*.css",
	"*.less",
	"*.scss",
	"*.vue",
	"*.html",
	"*/test_*",
	"*/node_modules/*",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]

FRAPPE_EXCLUSIONS = [
	"*/tests/*",
	"*/commands/*",
	"*/sparrow/change_log/*",
	"*/sparrow/exceptions*",
	"*/sparrow/coverage.py",
	"*sparrow/setup.py",
	"*/doctype/*/*_dashboard.py",
	"*/patches/*",
]


class CodeCoverage:
	def __init__(self, with_coverage, app):
		self.with_coverage = with_coverage
		self.app = app or "sparrow"

	def __enter__(self):
		if self.with_coverage:
			import os

			from coverage import Coverage

			from sparrow.utils import get_snova_path

			# Generate coverage report only for app that is being tested
			source_path = os.path.join(get_snova_path(), "apps", self.app)
			omit = STANDARD_EXCLUSIONS[:]

			if self.app == "sparrow":
				omit.extend(FRAPPE_EXCLUSIONS)

			self.coverage = Coverage(source=[source_path], omit=omit, include=STANDARD_INCLUSIONS)
			self.coverage.start()

	def __exit__(self, exc_type, exc_value, traceback):
		if self.with_coverage:
			self.coverage.stop()
			self.coverage.save()
			self.coverage.xml_report()
