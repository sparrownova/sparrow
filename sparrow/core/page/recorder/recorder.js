sparrow.pages["recorder"].on_page_load = function (wrapper) {
	sparrow.ui.make_app_page({
		parent: wrapper,
		title: __("Recorder"),
		single_column: true,
		card_layout: true,
	});

	sparrow.recorder = new Recorder(wrapper);
	$(wrapper).bind("show", function () {
		sparrow.recorder.show();
	});

	sparrow.require("recorder.bundle.js");
};

class Recorder {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.container = this.wrapper.find(".layout-main-section");
		this.container.append($('<div class="recorder-container"></div>'));
	}

	show() {
		if (!this.view || this.view.$route.name == "recorder-detail") return;
		this.view.$router.replace({ name: "recorder-detail" });
	}
}
