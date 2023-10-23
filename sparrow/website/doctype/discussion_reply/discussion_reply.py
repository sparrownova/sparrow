# Copyright (c) 2021, Sparrow Technologies and contributors
# For license information, please see license.txt

import sparrow
from sparrow.model.document import Document
from sparrow.realtime import get_website_room


class DiscussionReply(Document):
	def on_update(self):
		sparrow.publish_realtime(
			event="update_message",
			room=get_website_room(),
			message={"reply": sparrow.utils.md_to_html(self.reply), "reply_name": self.name},
			after_commit=True,
		)

	def after_insert(self):
		replies = sparrow.db.count("Discussion Reply", {"topic": self.topic})
		topic_info = sparrow.get_all(
			"Discussion Topic",
			{"name": self.topic},
			["reference_doctype", "reference_docname", "name", "title", "owner", "creation"],
		)

		template = sparrow.render_template(
			"sparrow/templates/discussions/reply_card.html",
			{
				"reply": self,
				"topic": {"name": self.topic},
				"loop": {"index": replies},
				"single_thread": True if not topic_info[0].title else False,
			},
		)

		sidebar = sparrow.render_template(
			"sparrow/templates/discussions/sidebar.html", {"topic": topic_info[0]}
		)

		new_topic_template = sparrow.render_template(
			"sparrow/templates/discussions/reply_section.html", {"topic": topic_info[0]}
		)

		sparrow.publish_realtime(
			event="publish_message",
			room=get_website_room(),
			message={
				"template": template,
				"topic_info": topic_info[0],
				"sidebar": sidebar,
				"new_topic_template": new_topic_template,
				"reply_owner": self.owner,
			},
			after_commit=True,
		)

	def after_delete(self):
		sparrow.publish_realtime(
			event="delete_message",
			room=get_website_room(),
			message={"reply_name": self.name},
			after_commit=True,
		)


@sparrow.whitelist()
def delete_message(reply_name):
	owner = sparrow.db.get_value("Discussion Reply", reply_name, "owner")
	if owner == sparrow.session.user:
		sparrow.delete_doc("Discussion Reply", reply_name)
