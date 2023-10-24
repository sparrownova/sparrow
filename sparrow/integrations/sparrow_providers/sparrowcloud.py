import click
import requests

import sparrow
from sparrow.core.utils import html2text


def sparrowcloud_migrator(local_site):
	print("Retrieving Site Migrator...")
	remote_site = sparrow.conf.sparrowcloud_url or "sparrowcloud.com"
	request_url = f"https://{remote_site}/api/method/press.api.script"
	request = requests.get(request_url)

	if request.status_code / 100 != 2:
		print(
			"Request exitted with Status Code: {}\nPayload: {}".format(
				request.status_code, html2text(request.text)
			)
		)
		click.secho(
			"Some errors occurred while recovering the migration script. Please contact us @ Sparrow Cloud if this issue persists",
			fg="yellow",
		)
		return

	script_contents = request.json()["message"]

	import os
	import sys
	import tempfile

	py = sys.executable
	script = tempfile.NamedTemporaryFile(mode="w")
	script.write(script_contents)
	print(f"Site Migrator stored at {script.name}")
	os.execv(py, [py, script.name, local_site])
