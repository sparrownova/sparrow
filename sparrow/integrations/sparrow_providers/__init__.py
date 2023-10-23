# imports - standard imports
import sys

# imports - module imports
from sparrow.integrations.frappe_providers.frappecloud import frappecloud_migrator


def migrate_to(local_site, frappe_provider):
	if frappe_provider in ("sparrow.cloud", "frappecloud.com"):
		return frappecloud_migrator(local_site)
	else:
		print(f"{frappe_provider} is not supported yet")
		sys.exit(1)
