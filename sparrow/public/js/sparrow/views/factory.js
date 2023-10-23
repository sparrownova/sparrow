// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.pages");
sparrow.provide("sparrow.views");

sparrow.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		this.route = sparrow.get_route();
		this.page_name = sparrow.get_route_str();

		if (this.before_show && this.before_show() === false) return;

		if (sparrow.pages[this.page_name]) {
			sparrow.container.change_to(this.page_name);
			if (this.on_show) {
				this.on_show();
			}
		} else {
			if (this.route[1]) {
				this.make(this.route);
			} else {
				sparrow.show_not_found(this.route);
			}
		}
	}

	make_page(double_column, page_name) {
		return sparrow.make_page(double_column, page_name);
	}
};

sparrow.make_page = function (double_column, page_name) {
	if (!page_name) {
		page_name = sparrow.get_route_str();
	}

	const page = sparrow.container.add_page(page_name);

	sparrow.ui.make_app_page({
		parent: page,
		single_column: !double_column,
	});

	sparrow.container.change_to(page_name);
	return page;
};
