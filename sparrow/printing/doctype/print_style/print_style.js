// Copyright (c) 2017, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Print Style", {
	refresh: function (frm) {
		frm.add_custom_button(__("Print Settings"), () => {
			sparrow.set_route("Form", "Print Settings");
		});
	},
});
