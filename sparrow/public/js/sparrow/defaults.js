// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.defaults = {
	get_user_default: function (key) {
		let defaults = sparrow.boot.user.defaults;
		let d = defaults[key];
		if (!d && sparrow.defaults.is_a_user_permission_key(key)) {
			d = defaults[sparrow.model.scrub(key)];
			// Check for default user permission values
			user_default = this.get_user_permission_default(key, defaults);
			if (user_default) d = user_default;
		}
		if ($.isArray(d)) d = d[0];

		if (!sparrow.defaults.in_user_permission(key, d)) {
			return;
		}

		return d;
	},

	get_user_permission_default: function (key, defaults) {
		let permissions = this.get_user_permissions();
		let user_default = null;
		if (permissions[key]) {
			permissions[key].forEach((item) => {
				if (defaults[key] == item.doc) {
					user_default = item.doc;
				}
			});

			permissions[key].forEach((item) => {
				if (item.is_default) {
					user_default = item.doc;
				}
			});
		}

		return user_default;
	},

	get_user_defaults: function (key) {
		var defaults = sparrow.boot.user.defaults;
		var d = defaults[key];

		if (sparrow.defaults.is_a_user_permission_key(key)) {
			if (d && $.isArray(d) && d.length === 1) {
				// Use User Permission value when only when it has a single value
				d = d[0];
			} else {
				d = defaults[key] || defaults[sparrow.model.scrub(key)];
			}
		}
		if (!$.isArray(d)) d = [d];

		// filter out values which are not permitted to the user
		d.filter((item) => {
			if (sparrow.defaults.in_user_permission(key, item)) {
				return item;
			}
		});
		return d;
	},
	get_global_default: function (key) {
		var d = sparrow.sys_defaults[key];
		if ($.isArray(d)) d = d[0];
		return d;
	},
	get_global_defaults: function (key) {
		var d = sparrow.sys_defaults[key];
		if (!$.isArray(d)) d = [d];
		return d;
	},
	set_user_default_local: function (key, value) {
		sparrow.boot.user.defaults[key] = value;
	},
	get_default: function (key) {
		var defaults = sparrow.boot.user.defaults;
		var value = defaults[key];
		if (sparrow.defaults.is_a_user_permission_key(key)) {
			if (value && $.isArray(value) && value.length === 1) {
				value = value[0];
			} else {
				value = defaults[sparrow.model.scrub(key)];
			}
		}

		if (!sparrow.defaults.in_user_permission(key, value)) {
			return;
		}

		if (value) {
			try {
				return JSON.parse(value);
			} catch (e) {
				return value;
			}
		}
	},

	is_a_user_permission_key: function (key) {
		return key.indexOf(":") === -1 && key !== sparrow.model.scrub(key);
	},

	in_user_permission: function (key, value) {
		let user_permission = this.get_user_permissions()[sparrow.model.unscrub(key)];

		if (user_permission && user_permission.length) {
			let doc_found = user_permission.some((perm) => {
				return perm.doc === value;
			});
			return doc_found;
		} else {
			// there is no user permission for this doctype
			// so we can allow this doc i.e., value
			return true;
		}
	},

	get_user_permissions: function () {
		return this._user_permissions || {};
	},

	update_user_permissions: function () {
		const method = "sparrow.core.doctype.user_permission.user_permission.get_user_permissions";
		sparrow.call(method).then((r) => {
			if (r.message) {
				this._user_permissions = Object.assign({}, r.message);
			}
		});
	},

	load_user_permission_from_boot: function () {
		if (sparrow.boot.user.user_permissions) {
			this._user_permissions = Object.assign({}, sparrow.boot.user.user_permissions);
		} else {
			sparrow.defaults.update_user_permissions();
		}
	},
};
