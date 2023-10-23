// Copyright (c) 2016, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Contact", {
	onload(frm) {
		frm.email_field = "email_id";
	},
	refresh: function (frm) {
		if (frm.doc.__islocal) {
			const last_doc = sparrow.contacts.get_last_doc(frm);
			if (
				sparrow.dynamic_link &&
				sparrow.dynamic_link.doc &&
				sparrow.dynamic_link.doc.name == last_doc.docname
			) {
				frm.set_value("links", "");
				frm.add_child("links", {
					link_doctype: sparrow.dynamic_link.doctype,
					link_name: sparrow.dynamic_link.doc[sparrow.dynamic_link.fieldname],
				});
			}
		}

		if (!frm.doc.user && !frm.is_new() && frm.perm[0].write) {
			frm.add_custom_button(__("Invite as User"), function () {
				return sparrow.call({
					method: "sparrow.contacts.doctype.contact.contact.invite_user",
					args: {
						contact: frm.doc.name,
					},
					callback: function (r) {
						frm.set_value("user", r.message);
					},
				});
			});
		}
		frm.set_query("link_doctype", "links", function () {
			return {
				query: "sparrow.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: "HTML",
					fieldname: "contact_html",
				},
			};
		});
		frm.refresh_field("links");

		let numbers = frm.doc.phone_nos;
		if (numbers && numbers.length && sparrow.phone_call.handler) {
			frm.add_custom_button(__("Call"), () => {
				numbers = frm.doc.phone_nos
					.sort((prev, next) => next.is_primary_mobile_no - prev.is_primary_mobile_no)
					.map((d) => d.phone);
				sparrow.phone_call.handler(numbers);
			});
		}

		if (frm.doc.links) {
			sparrow.call({
				method: "sparrow.contacts.doctype.contact.contact.address_query",
				args: { links: frm.doc.links },
				callback: function (r) {
					if (r && r.message) {
						frm.set_query("address", function () {
							return {
								filters: {
									name: ["in", r.message],
								},
							};
						});
					}
				},
			});

			for (let i in frm.doc.links) {
				let link = frm.doc.links[i];
				frm.add_custom_button(
					__("{0}: {1}", [__(link.link_doctype), __(link.link_name)]),
					function () {
						sparrow.set_route("Form", link.link_doctype, link.link_name);
					},
					__("Links")
				);
			}
		}
	},
	validate: function (frm) {
		// clear linked customer / supplier / sales partner on saving...
		if (frm.doc.links) {
			frm.doc.links.forEach(function (d) {
				sparrow.model.remove_from_locals(d.link_doctype, d.link_name);
			});
		}
	},
	after_save: function (frm) {
		sparrow.run_serially([
			() => sparrow.timeout(1),
			() => {
				const last_doc = sparrow.contacts.get_last_doc(frm);
				if (
					sparrow.dynamic_link &&
					sparrow.dynamic_link.doc &&
					sparrow.dynamic_link.doc.name == last_doc.docname
				) {
					for (let i in frm.doc.links) {
						let link = frm.doc.links[i];
						if (
							last_doc.doctype == link.link_doctype &&
							last_doc.docname == link.link_name
						) {
							sparrow.set_route("Form", last_doc.doctype, last_doc.docname);
						}
					}
				}
			},
		]);
	},
	sync_with_google_contacts: function (frm) {
		if (frm.doc.sync_with_google_contacts) {
			sparrow.db.get_value(
				"Google Contacts",
				{ email_id: sparrow.session.user },
				"name",
				(r) => {
					if (r && r.name) {
						frm.set_value("google_contacts", r.name);
					}
				}
			);
		}
	},
});

sparrow.ui.form.on("Dynamic Link", {
	link_name: function (frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if (child.link_name) {
			sparrow.model.with_doctype(child.link_doctype, function () {
				var title_field = sparrow.get_meta(child.link_doctype).title_field || "name";
				sparrow.model.get_value(
					child.link_doctype,
					child.link_name,
					title_field,
					function (r) {
						sparrow.model.set_value(cdt, cdn, "link_title", r[title_field]);
					}
				);
			});
		}
	},
});
