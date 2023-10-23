// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Google Settings", {
	refresh: function (frm) {
		frm.dashboard.set_headline(
			__("For more information, {0}.", [
				`<a href='https://shopper.com/docs/user/manual/en/shopper_integration/google_settings'>${__(
					"Click here"
				)}</a>`,
			])
		);
	},
});
