# Copyright (c) 2022, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import json
import os
from textwrap import dedent

import sparrow
import sparrow.model.sync
import sparrow.modules.patch_handler
import sparrow.translate
from sparrow.cache_manager import clear_global_cache
from sparrow.core.doctype.language.language import sync_languages
from sparrow.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from sparrow.database.schema import add_column
from sparrow.deferred_insert import save_to_db as flush_deferred_inserts
from sparrow.desk.notifications import clear_notifications
from sparrow.modules.patch_handler import PatchType
from sparrow.modules.utils import sync_customizations
from sparrow.search.website_search import build_index_for_all_routes
from sparrow.utils.connections import check_connection
from sparrow.utils.dashboard import sync_dashboards
from sparrow.utils.fixtures import sync_fixtures
from sparrow.website.utils import clear_website_cache

snova_START_MESSAGE = dedent(
	"""
	Cannot run snova migrate without the services running.
	If you are running snova in development mode, make sure that snova is running:

	$ snova start

	Otherwise, check the server logs and ensure that all the required services are running.
	"""
)


def atomic(method):
	def wrapper(*args, **kwargs):
		try:
			ret = method(*args, **kwargs)
			sparrow.db.commit()
			return ret
		except Exception:
			sparrow.db.rollback()
			raise

	return wrapper


class SiteMigration:
	"""Migrate all apps to the current version, will:
	- run before migrate hooks
	- run patches
	- sync doctypes (schema)
	- sync dashboards
	- sync jobs
	- sync fixtures
	- sync customizations
	- sync languages
	- sync web pages (from /www)
	- run after migrate hooks
	"""

	def __init__(self, skip_failing: bool = False, skip_search_index: bool = False) -> None:
		self.skip_failing = skip_failing
		self.skip_search_index = skip_search_index

	def setUp(self):
		"""Complete setup required for site migration"""
		sparrow.flags.touched_tables = set()
		self.touched_tables_file = sparrow.get_site_path("touched_tables.json")
		add_column(doctype="DocType", column_name="migration_hash", fieldtype="Data")
		clear_global_cache()

		if os.path.exists(self.touched_tables_file):
			os.remove(self.touched_tables_file)

		sparrow.flags.in_migrate = True

	def tearDown(self):
		"""Run operations that should be run post schema updation processes
		This should be executed irrespective of outcome
		"""
		sparrow.translate.clear_cache()
		clear_website_cache()
		clear_notifications()

		with open(self.touched_tables_file, "w") as f:
			json.dump(list(sparrow.flags.touched_tables), f, sort_keys=True, indent=4)

		if not self.skip_search_index:
			print(f"Queued rebuilding of search index for {sparrow.local.site}")
			sparrow.enqueue(build_index_for_all_routes, queue="long")

		sparrow.publish_realtime("version-update")
		sparrow.flags.touched_tables.clear()
		sparrow.flags.in_migrate = False

	@atomic
	def pre_schema_updates(self):
		"""Executes `before_migrate` hooks"""
		for app in sparrow.get_installed_apps():
			for fn in sparrow.get_hooks("before_migrate", app_name=app):
				sparrow.get_attr(fn)()

	@atomic
	def run_schema_updates(self):
		"""Run patches as defined in patches.txt, sync schema changes as defined in the {doctype}.json files"""
		sparrow.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.pre_model_sync
		)
		sparrow.model.sync.sync_all()
		sparrow.modules.patch_handler.run_all(
			skip_failing=self.skip_failing, patch_type=PatchType.post_model_sync
		)

	@atomic
	def post_schema_updates(self):
		"""Execute pending migration tasks post patches execution & schema sync
		This includes:
		* Sync `Scheduled Job Type` and scheduler events defined in hooks
		* Sync fixtures & custom scripts
		* Sync in-Desk Module Dashboards
		* Sync customizations: Custom Fields, Property Setters, Custom Permissions
		* Sync Sparrow's internal language master
		* Flush deferred inserts made during maintenance mode.
		* Sync Portal Menu Items
		* Sync Installed Applications Version History
		* Execute `after_migrate` hooks
		"""
		sync_jobs()
		sync_fixtures()
		sync_dashboards()
		sync_customizations()
		sync_languages()
		flush_deferred_inserts()

		sparrow.get_single("Portal Settings").sync_menu()
		sparrow.get_single("Installed Applications").update_versions()

		for app in sparrow.get_installed_apps():
			for fn in sparrow.get_hooks("after_migrate", app_name=app):
				sparrow.get_attr(fn)()

	def required_services_running(self) -> bool:
		"""Returns True if all required services are running. Returns False and prints
		instructions to stdout when required services are not available.
		"""
		service_status = check_connection(redis_services=["redis_cache"])
		are_services_running = all(service_status.values())

		if not are_services_running:
			for service in service_status:
				if not service_status.get(service, True):
					print(f"Service {service} is not running.")
			print(snova_START_MESSAGE)

		return are_services_running

	def run(self, site: str):
		"""Run Migrate operation on site specified. This method initializes
		and destroys connections to the site database.
		"""
		if site:
			sparrow.init(site=site)
			sparrow.connect()

		if not self.required_services_running():
			raise SystemExit(1)

		self.setUp()
		try:
			self.pre_schema_updates()
			self.run_schema_updates()
			self.post_schema_updates()
		finally:
			self.tearDown()
			sparrow.destroy()
