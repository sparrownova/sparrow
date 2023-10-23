// Copyright (c) 2015, Sparrow Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

sparrow.provide("sparrow.workflow");

sparrow.workflow = {
	state_fields: {},
	workflows: {},
	setup: function (doctype) {
		var wf = sparrow.get_list("Workflow", { document_type: doctype });
		if (wf.length) {
			sparrow.workflow.workflows[doctype] = wf[0];
			sparrow.workflow.state_fields[doctype] = wf[0].workflow_state_field;
		} else {
			sparrow.workflow.state_fields[doctype] = null;
		}
	},
	get_state_fieldname: function (doctype) {
		if (sparrow.workflow.state_fields[doctype] === undefined) {
			sparrow.workflow.setup(doctype);
		}
		return sparrow.workflow.state_fields[doctype];
	},
	get_default_state: function (doctype, docstatus) {
		sparrow.workflow.setup(doctype);
		var value = null;
		$.each(sparrow.workflow.workflows[doctype].states, function (i, workflow_state) {
			if (cint(workflow_state.doc_status) === cint(docstatus)) {
				value = workflow_state.state;
				return false;
			}
		});
		return value;
	},
	get_transitions: function (doc) {
		sparrow.workflow.setup(doc.doctype);
		return sparrow.xcall("sparrow.model.workflow.get_transitions", { doc: doc });
	},
	get_document_state_roles: function (doctype, state) {
		sparrow.workflow.setup(doctype);
		let workflow_states =
			sparrow.get_children(sparrow.workflow.workflows[doctype], "states", { state: state }) ||
			[];
		let allow_edit_list = workflow_states.map((d) => d.allow_edit);
		return allow_edit_list;
	},
	is_self_approval_enabled: function (doctype) {
		return sparrow.workflow.workflows[doctype].allow_self_approval;
	},
	is_read_only: function (doctype, name) {
		var state_fieldname = sparrow.workflow.get_state_fieldname(doctype);
		if (state_fieldname) {
			var doc = locals[doctype][name];
			if (!doc) return false;
			if (doc.__islocal) return false;

			var state =
				doc[state_fieldname] || sparrow.workflow.get_default_state(doctype, doc.docstatus);

			let allow_edit_roles = state
				? sparrow.workflow.get_document_state_roles(doctype, state)
				: null;
			let has_common_role = sparrow.user_roles.some((role) =>
				allow_edit_roles.includes(role)
			);
			return !has_common_role;
		}
		return false;
	},
	get_update_fields: function (doctype) {
		var update_fields = $.unique(
			$.map(sparrow.workflow.workflows[doctype].states || [], function (d) {
				return d.update_field;
			})
		);
		return update_fields;
	},
	get_state(doc) {
		const state_field = this.get_state_fieldname(doc.doctype);
		let state = doc[state_field];
		if (!state) {
			state = this.get_default_state(doc.doctype, doc.docstatus);
		}
		return state;
	},
	get_all_transitions(doctype) {
		return sparrow.workflow.workflows[doctype].transitions || [];
	},
	get_all_transition_actions(doctype) {
		const transitions = this.get_all_transitions(doctype);
		return transitions.map((transition) => {
			return transition.action;
		});
	},
};
