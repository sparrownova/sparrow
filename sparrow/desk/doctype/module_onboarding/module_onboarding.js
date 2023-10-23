// Copyright (c) 2020, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Module Onboarding", {
	refresh: function (frm) {
		sparrow.boot.developer_mode &&
			frm.set_intro(
				__(
					"Saving this will export this document as well as the steps linked here as json."
				),
				true
			);
		if (!sparrow.boot.developer_mode) {
			frm.trigger("disable_form");
		}
	},

	disable_form: function (frm) {
		frm.set_read_only();
		frm.fields
			.filter((field) => field.has_input)
			.forEach((field) => {
				frm.set_df_property(field.df.fieldname, "read_only", "1");
			});
		frm.disable_save();
	},
});
