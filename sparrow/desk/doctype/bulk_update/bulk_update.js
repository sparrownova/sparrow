// Copyright (c) 2016, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Bulk Update", {
	refresh: function (frm) {
		frm.set_query("document_type", function () {
			return {
				filters: [
					["DocType", "issingle", "=", 0],
					["DocType", "name", "not in", sparrow.model.core_doctypes_list],
				],
			};
		});

		frm.page.set_primary_action(__("Update"), function () {
			if (!frm.doc.update_value) {
				sparrow.throw(__('Field "value" is mandatory. Please specify value to be updated'));
			} else {
				frm.call("bulk_update").then((r) => {
					let failed = r.message;
					if (!failed) failed = [];

					if (failed.length && !r._server_messages) {
						sparrow.throw(
							__("Cannot update {0}", [
								failed.map((f) => (f.bold ? f.bold() : f)).join(", "),
							])
						);
					} else {
						sparrow.msgprint({
							title: __("Success"),
							message: __("Updated Successfully"),
							indicator: "green",
						});
					}

					sparrow.hide_progress();
					frm.save();
				});
			}
		});
	},

	document_type: function (frm) {
		// set field options
		if (!frm.doc.document_type) return;

		sparrow.model.with_doctype(frm.doc.document_type, function () {
			var options = $.map(sparrow.get_meta(frm.doc.document_type).fields, function (d) {
				if (d.fieldname && sparrow.model.no_value_type.indexOf(d.fieldtype) === -1) {
					return d.fieldname;
				}
				return null;
			});
			frm.set_df_property("field", "options", options);
		});
	},
});
