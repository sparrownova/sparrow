// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.views.formview");

sparrow.views.FormFactory = class FormFactory extends sparrow.views.Factory {
	make(route) {
		var doctype = route[1],
			doctype_layout = sparrow.router.doctype_layout || doctype;

		if (!sparrow.views.formview[doctype_layout]) {
			sparrow.model.with_doctype(doctype, () => {
				this.page = sparrow.container.add_page(doctype_layout);
				sparrow.views.formview[doctype_layout] = this.page;
				this.make_and_show(doctype, route);
			});
		} else {
			this.show_doc(route);
		}

		this.setup_events();
	}

	make_and_show(doctype, route) {
		if (sparrow.router.doctype_layout) {
			sparrow.model.with_doc("DocType Layout", sparrow.router.doctype_layout, () => {
				this.make_form(doctype);
				this.show_doc(route);
			});
		} else {
			this.make_form(doctype);
			this.show_doc(route);
		}
	}

	make_form(doctype) {
		this.page.frm = new sparrow.ui.form.Form(
			doctype,
			this.page,
			true,
			sparrow.router.doctype_layout
		);
	}

	setup_events() {
		if (!this.initialized) {
			$(document).on("page-change", function () {
				sparrow.ui.form.close_grid_form();
			});

			sparrow.realtime.on("doc_viewers", function (data) {
				// set users that currently viewing the form
				sparrow.ui.form.FormViewers.set_users(data, "viewers");
			});

			sparrow.realtime.on("doc_typers", function (data) {
				// set users that currently typing on the form
				sparrow.ui.form.FormViewers.set_users(data, "typers");
			});
		}
		this.initialized = true;
	}

	show_doc(route) {
		var doctype = route[1],
			doctype_layout = sparrow.router.doctype_layout || doctype,
			name = route.slice(2).join("/");

		if (sparrow.model.new_names[name]) {
			// document has been renamed, reroute
			name = sparrow.model.new_names[name];
			sparrow.set_route("Form", doctype_layout, name);
			return;
		}

		const doc = sparrow.get_doc(doctype, name);
		if (
			doc &&
			sparrow.model.get_docinfo(doctype, name) &&
			(doc.__islocal || sparrow.model.is_fresh(doc))
		) {
			// is document available and recent?
			this.render(doctype_layout, name);
		} else {
			this.fetch_and_render(doctype, name, doctype_layout);
		}
	}

	fetch_and_render(doctype, name, doctype_layout) {
		sparrow.model.with_doc(doctype, name, (name, r) => {
			if (r && r["403"]) return; // not permitted

			if (!(locals[doctype] && locals[doctype][name])) {
				if (name && name.substr(0, 3) === "new") {
					this.render_new_doc(doctype, name, doctype_layout);
				} else {
					sparrow.show_not_found();
				}
				return;
			}
			this.render(doctype_layout, name);
		});
	}

	render_new_doc(doctype, name, doctype_layout) {
		const new_name = sparrow.model.make_new_doc_and_get_name(doctype, true);
		if (new_name === name) {
			this.render(doctype_layout, name);
		} else {
			sparrow.route_flags.replace_route = true;
			sparrow.set_route("Form", doctype_layout, new_name);
		}
	}

	render(doctype_layout, name) {
		sparrow.container.change_to(doctype_layout);
		sparrow.views.formview[doctype_layout].frm.refresh(name);
	}
};
