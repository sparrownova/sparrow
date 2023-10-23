sparrow.ui.form.ControlText = class ControlText extends sparrow.ui.form.ControlData {
	static html_element = "textarea";
	static horizontal = false;
	make_wrapper() {
		super.make_wrapper();
		this.$wrapper.find(".like-disabled-input").addClass("for-description");
	}
	make_input() {
		super.make_input();
		this.$input.css({ height: "300px" });
		if (this.df.max_height) {
			this.$input.css({ "max-height": this.df.max_height });
		}
	}
};

sparrow.ui.form.ControlLongText = sparrow.ui.form.ControlText;
sparrow.ui.form.ControlSmallText = class ControlSmallText extends sparrow.ui.form.ControlText {
	make_input() {
		super.make_input();
		this.$input.css({ height: "150px" });
	}
};
