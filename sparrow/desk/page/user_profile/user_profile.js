sparrow.pages["user-profile"].on_page_load = function (wrapper) {
	sparrow.require("user_profile_controller.bundle.js", () => {
		let user_profile = new sparrow.ui.UserProfile(wrapper);
		user_profile.show();
	});
};
