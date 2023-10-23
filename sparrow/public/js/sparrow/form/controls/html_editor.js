sparrow.ui.form.ControlHTMLEditor = class ControlHTMLEditor extends (
	sparrow.ui.form.ControlMarkdownEditor
) {
	static editor_class = "html";
	set_language() {
		this.df.options = "HTML";
		super.set_language();
	}
	update_preview() {
		if (!this.markdown_preview) return;
		let value = this.get_value() || "";
		value = sparrow.dom.remove_script_and_style(value);
		this.markdown_preview.html(value);
	}
};
