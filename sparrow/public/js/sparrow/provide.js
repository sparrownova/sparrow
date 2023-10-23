// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if (!window.sparrow) window.sparrow = {};

sparrow.provide = function (namespace) {
	// docs: create a namespace //
	var nsl = namespace.split(".");
	var parent = window;
	for (var i = 0; i < nsl.length; i++) {
		var n = nsl[i];
		if (!parent[n]) {
			parent[n] = {};
		}
		parent = parent[n];
	}
	return parent;
};

sparrow.provide("locals");
sparrow.provide("sparrow.flags");
sparrow.provide("sparrow.settings");
sparrow.provide("sparrow.utils");
sparrow.provide("sparrow.ui.form");
sparrow.provide("sparrow.modules");
sparrow.provide("sparrow.templates");
sparrow.provide("sparrow.test_data");
sparrow.provide("sparrow.utils");
sparrow.provide("sparrow.model");
sparrow.provide("sparrow.user");
sparrow.provide("sparrow.session");
sparrow.provide("sparrow._messages");
sparrow.provide("locals.DocType");

// for listviews
sparrow.provide("sparrow.listview_settings");
sparrow.provide("sparrow.tour");
sparrow.provide("sparrow.listview_parent_route");

// constants
window.NEWLINE = "\n";
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm = null;
