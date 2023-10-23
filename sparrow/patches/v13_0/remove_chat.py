import click

import sparrow


def execute():
	sparrow.delete_doc_if_exists("DocType", "Chat Message")
	sparrow.delete_doc_if_exists("DocType", "Chat Message Attachment")
	sparrow.delete_doc_if_exists("DocType", "Chat Profile")
	sparrow.delete_doc_if_exists("DocType", "Chat Token")
	sparrow.delete_doc_if_exists("DocType", "Chat Room User")
	sparrow.delete_doc_if_exists("DocType", "Chat Room")
	sparrow.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from Sparrow in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/sparrownova/chat",
		fg="yellow",
	)
