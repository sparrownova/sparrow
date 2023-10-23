# imports - standard imports
import sys

# imports - module imports
from sparrow.integrations.sparrow_providers.sparrowcloud import sparrowcloud_migrator


def migrate_to(local_site, sparrow_provider):
	if sparrow_provider in ("sparrow.cloud", "sparrowcloud.com"):
		return sparrowcloud_migrator(local_site)
	else:
		print(f"{sparrow_provider} is not supported yet")
		sys.exit(1)
