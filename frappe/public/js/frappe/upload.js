// Copyright (c) 2015, Sparrownova Technologies and Contributors
// MIT License. See license.txt

if (frappe.require) {
	frappe.require("file_uploader.bundle.js");
} else {
	frappe.ready(function () {
		frappe.require("file_uploader.bundle.js");
	});
}
