# Copyright (c) 2021, Sparrow Technologies and contributors
# For license information, please see license.txt

import sparrow
from sparrow import _
from sparrow.model.document import Document


class NetworkPrinterSettings(Document):
	@sparrow.whitelist()
	def get_printers_list(self, ip="127.0.0.1", port=631):
		printer_list = []
		try:
			import cups
		except ImportError:
			sparrow.throw(
				_(
					"""This feature can not be used as dependencies are missing.
				Please contact your system manager to enable this by installing pycups!"""
				)
			)
			return
		try:
			cups.setServer(self.server_ip)
			cups.setPort(self.port)
			conn = cups.Connection()
			printers = conn.getPrinters()
			for printer_id, printer in printers.items():
				printer_list.append({"value": printer_id, "label": printer["printer-make-and-model"]})

		except RuntimeError:
			sparrow.throw(_("Failed to connect to server"))
		except sparrow.ValidationError:
			sparrow.throw(_("Failed to connect to server"))
		return printer_list


@sparrow.whitelist()
def get_network_printer_settings():
	return sparrow.db.get_list("Network Printer Settings", pluck="name")
