sparrow.ui.form.ControlHeading = class ControlHeading extends sparrow.ui.form.ControlHTML {
	get_content() {
		return "<h4>" + __(this.df.label) + "</h4>";
	}
};
