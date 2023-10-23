sparrow.user_info = function (uid) {
	if (!uid) uid = sparrow.session.user;

	if (!(sparrow.boot.user_info && sparrow.boot.user_info[uid])) {
		var user_info = { fullname: uid || "Unknown" };
	} else {
		var user_info = sparrow.boot.user_info[uid];
	}

	user_info.abbr = sparrow.get_abbr(user_info.fullname);
	user_info.color = sparrow.get_palette(user_info.fullname);

	return user_info;
};

sparrow.update_user_info = function (user_info) {
	for (let user in user_info) {
		if (sparrow.boot.user_info[user]) {
			Object.assign(sparrow.boot.user_info[user], user_info[user]);
		} else {
			sparrow.boot.user_info[user] = user_info[user];
		}
	}
};

sparrow.provide("sparrow.user");

$.extend(sparrow.user, {
	name: "Guest",
	full_name: function (uid) {
		return uid === sparrow.session.user
			? __(
					"You",
					null,
					"Name of the current user. For example: You edited this 5 hours ago."
			  )
			: sparrow.user_info(uid).fullname;
	},
	image: function (uid) {
		return sparrow.user_info(uid).image;
	},
	abbr: function (uid) {
		return sparrow.user_info(uid).abbr;
	},
	has_role: function (rl) {
		if (typeof rl == "string") rl = [rl];
		for (var i in rl) {
			if ((sparrow.boot ? sparrow.boot.user.roles : ["Guest"]).indexOf(rl[i]) != -1)
				return true;
		}
	},
	get_desktop_items: function () {
		// hide based on permission
		var modules_list = $.map(sparrow.boot.allowed_modules, function (icon) {
			var m = icon.module_name;
			var type = sparrow.modules[m] && sparrow.modules[m].type;

			if (sparrow.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if (sparrow.boot.user.allow_modules.indexOf(m) != -1 || sparrow.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if (sparrow.boot.allowed_pages.indexOf(sparrow.modules[m].link) != -1) ret = m;
			} else if (type === "list") {
				if (sparrow.model.can_read(sparrow.modules[m]._doctype)) ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if (
					sparrow.user.has_role("System Manager") ||
					sparrow.user.has_role("Administrator")
				)
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function () {
		return sparrow.user.has_role(["Administrator", "System Manager", "Report Manager"]);
	},

	get_formatted_email: function (email) {
		var fullname = sparrow.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = "";

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl("%(quote)s%(fullname)s%(quote)s <%(email)s>", {
				fullname: fullname,
				email: email,
				quote: quote,
			});
		}
	},

	get_emails: () => {
		return Object.keys(sparrow.boot.user_info).map((key) => sparrow.boot.user_info[key].email);
	},

	/* Normally sparrow.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (sparrow.user === 'Administrator')
	 *
	 * sparrow.user will cast to a string
	 * returning sparrow.user.name
	 */
	toString: function () {
		return this.name;
	},
});

sparrow.session_alive = true;
$(document).bind("mousemove", function () {
	if (sparrow.session_alive === false) {
		$(document).trigger("session_alive");
	}
	sparrow.session_alive = true;
	if (sparrow.session_alive_timeout) clearTimeout(sparrow.session_alive_timeout);
	sparrow.session_alive_timeout = setTimeout("sparrow.session_alive=false;", 30000);
});
