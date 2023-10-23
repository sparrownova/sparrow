import click


def execute():
	click.secho(
		"Event Streaming is moved to a separate app in version 15.\n"
		"When upgrading to Sparrow version-15, Please install the 'Event Streaming' app to continue using them: https://github.com/sparrownova/event_streaming",
		fg="yellow",
	)
