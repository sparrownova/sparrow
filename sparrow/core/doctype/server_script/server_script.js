// Copyright (c) 2019, Sparrow Technologies and contributors
// For license information, please see license.txt

sparrow.ui.form.on("Server Script", {
	setup: function (frm) {
		frm.trigger("setup_help");
	},
	refresh: function (frm) {
		if (frm.doc.script_type != "Scheduler Event") {
			frm.dashboard.hide();
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__("Compare Versions"), () => {
				new sparrow.ui.DiffView("Server Script", "script", frm.doc.name);
			});
		}

		frm.call("get_autocompletion_items")
			.then((r) => r.message)
			.then((items) => {
				frm.set_df_property("script", "autocompletions", items);
			});
	},

	setup_help(frm) {
		frm.get_field("help_html").html(`
<h4>DocType Event</h4>
<p>Add logic for standard doctype events like Before Insert, After Submit, etc.</p>
<pre>
	<code>
# set property
if "test" in doc.description:
	doc.status = 'Closed'


# validate
if "validate" in doc.description:
	raise sparrow.ValidationError

# auto create another document
if doc.allocated_to:
	sparrow.get_doc(dict(
		doctype = 'ToDo'
		owner = doc.allocated_to,
		description = doc.subject
	)).insert()
</code>
</pre>

<hr>

<h4>API Call</h4>
<p>Respond to <code>/api/method/&lt;method-name&gt;</code> calls, just like whitelisted methods</p>
<pre><code>
# respond to API

if sparrow.form_dict.message == "ping":
	sparrow.response['message'] = "pong"
else:
	sparrow.response['message'] = "ok"
</code></pre>

<hr>

<h4>Permission Query</h4>
<p>Add conditions to the where clause of list queries.</p>
<pre><code>
# generate dynamic conditions and set it in the conditions variable
tenant_id = sparrow.db.get_value(...)
conditions = 'tenant_id = {}'.format(tenant_id)

# resulting select query
select name from \`tabPerson\`
where tenant_id = 2
order by creation desc
</code></pre>
`);
	},
});
