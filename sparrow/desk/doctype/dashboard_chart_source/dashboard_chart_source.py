# Copyright (c) 2019, Sparrow Technologies and contributors
# License: MIT. See LICENSE

import os

import sparrow
from sparrow.model.document import Document
from sparrow.modules import get_module_path, scrub
from sparrow.modules.export_file import export_to_files


@sparrow.whitelist()
def get_config(name):
	doc = sparrow.get_doc("Dashboard Chart Source", name)
	with open(
		os.path.join(
			get_module_path(doc.module), "dashboard_chart_source", scrub(doc.name), scrub(doc.name) + ".js"
		),
	) as f:
		return f.read()


class DashboardChartSource(Document):
	def on_update(self):
		export_to_files(
			record_list=[[self.doctype, self.name]], record_module=self.module, create_init=True
		)
