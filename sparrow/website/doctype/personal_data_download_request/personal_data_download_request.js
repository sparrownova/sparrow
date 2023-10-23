// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Personal Data Download Request", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.doc.user = sparrow.session.user;
		}
	},
});
