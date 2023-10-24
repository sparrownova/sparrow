# Copyright (c) 2022, Sparrow Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# imports - standard imports
import gzip
import importlib
import json
import os
import shlex
import subprocess
import unittest
from contextlib import contextmanager
from functools import wraps
from glob import glob
from pathlib import Path
from unittest.case import skipIf
from unittest.mock import patch

# imports - third party imports
import click
from click import Command
from click.testing import CliRunner, Result

# imports - module imports
import sparrow
import sparrow.commands.site
import sparrow.commands.utils
import sparrow.recorder
from sparrow.installer import add_to_installed_apps, remove_app
from sparrow.query_builder.utils import db_type_is
from sparrow.tests.test_query_builder import run_only_if
from sparrow.tests.utils import sparrowTestCase, timeout
from sparrow.utils import add_to_date, get_bench_path, get_bench_relative_path, now
from sparrow.utils.backups import BackupGenerator, fetch_latest_backups
from sparrow.utils.jinja_globals import bundled_asset
from sparrow.utils.scheduler import enable_scheduler, is_scheduler_inactive

_result: Result | None = None
TEST_SITE = "commands-site-O4PN2QKA.test"  # added random string tag to avoid collisions
CLI_CONTEXT = sparrow._dict(sites=[TEST_SITE])


def clean(value) -> str:
	"""Strips and converts bytes to str

	Args:
	        value ([type]): [description]

	Returns:
	        [type]: [description]
	"""
	if isinstance(value, bytes):
		value = value.decode()
	if isinstance(value, str):
		value = value.strip()
	return value


def missing_in_backup(doctypes: list, file: os.PathLike) -> list:
	"""Returns list of missing doctypes in the backup.

	Args:
	        doctypes (list): List of DocTypes to be checked
	        file (str): Path of the database file

	Returns:
	        doctypes(list): doctypes that are missing in backup
	"""
	predicate = 'COPY public."tab{}"' if sparrow.conf.db_type == "postgres" else "CREATE TABLE `tab{}`"
	with gzip.open(file, "rb") as f:
		content = f.read().decode("utf8").lower()

	return [doctype for doctype in doctypes if predicate.format(doctype).lower() not in content]


def exists_in_backup(doctypes: list, file: os.PathLike) -> bool:
	"""Checks if the list of doctypes exist in the database.sql.gz file supplied

	Args:
	        doctypes (list): List of DocTypes to be checked
	        file (str): Path of the database file

	Returns:
	        bool: True if all tables exist
	"""
	missing_doctypes = missing_in_backup(doctypes, file)
	return len(missing_doctypes) == 0


@contextmanager
def maintain_locals():
	pre_site = sparrow.local.site
	pre_flags = sparrow.local.flags.copy()
	pre_db = sparrow.local.db

	try:
		yield
	finally:
		post_site = getattr(sparrow.local, "site", None)
		if not post_site or post_site != pre_site:
			sparrow.init(site=pre_site)
			sparrow.local.db = pre_db
			sparrow.local.flags.update(pre_flags)


def pass_test_context(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		return f(CLI_CONTEXT, *args, **kwargs)

	return decorated_function


@contextmanager
def cli(cmd: Command, args: list | None = None):
	with maintain_locals():
		global _result

		patch_ctx = patch("sparrow.commands.pass_context", pass_test_context)
		_module = cmd.callback.__module__
		_cmd = cmd.callback.__qualname__

		__module = importlib.import_module(_module)
		patch_ctx.start()
		importlib.reload(__module)
		click_cmd = getattr(__module, _cmd)

		try:
			_result = CliRunner().invoke(click_cmd, args=args)
			_result.command = str(cmd)
			yield _result
		finally:
			patch_ctx.stop()
			__module = importlib.import_module(_module)
			importlib.reload(__module)
			importlib.invalidate_caches()


class BaseTestCommands(sparrowTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		cls.setup_test_site()

	@classmethod
	def execute(self, command, kwargs=None):
		# tests might have written to DB which wont be visible to commands until we end current transaction
		sparrow.db.commit()

		site = {"site": sparrow.local.site}
		cmd_input = None
		if kwargs:
			cmd_input = kwargs.get("cmd_input", None)
			if cmd_input:
				if not isinstance(cmd_input, bytes):
					raise Exception(f"The input should be of type bytes, not {type(cmd_input).__name__}")

				del kwargs["cmd_input"]
			kwargs.update(site)
		else:
			kwargs = site

		self.command = " ".join(command.split()).format(**kwargs)
		click.secho(self.command, fg="bright_black")

		command = shlex.split(self.command)
		self._proc = subprocess.run(command, input=cmd_input, capture_output=True)
		self.stdout = clean(self._proc.stdout)
		self.stderr = clean(self._proc.stderr)
		self.returncode = clean(self._proc.returncode)

		# Commands might have written to DB which wont be visible until we end current transaction
		sparrow.db.rollback()

	@classmethod
	def setup_test_site(cls):
		cmd_config = {
			"test_site": TEST_SITE,
			"admin_password": sparrow.conf.admin_password,
			"root_login": sparrow.conf.root_login,
			"root_password": sparrow.conf.root_password,
			"db_type": sparrow.conf.db_type,
		}

		if not os.path.exists(os.path.join(TEST_SITE, "site_config.json")):
			cls.execute(
				"snova new-site {test_site} --admin-password {admin_password} --db-type" " {db_type}",
				cmd_config,
			)

	def _formatMessage(self, msg, standardMsg):
		output = super()._formatMessage(msg, standardMsg)

		if not hasattr(self, "command") and _result:
			command = _result.command
			stdout = _result.stdout_bytes.decode() if _result.stdout_bytes else None
			stderr = _result.stderr_bytes.decode() if _result.stderr_bytes else None
			returncode = _result.exit_code
		else:
			command = self.command
			stdout = self.stdout
			stderr = self.stderr
			returncode = self.returncode

		cmd_execution_summary = "\n".join(
			[
				"-" * 70,
				"Last Command Execution Summary:",
				f"Command: {command}" if command else "",
				f"Standard Output: {stdout}" if stdout else "",
				f"Standard Error: {stderr}" if stderr else "",
				f"Return Code: {returncode}" if returncode else "",
			]
		).strip()

		return f"{output}\n\n{cmd_execution_summary}"


class TestCommands(BaseTestCommands):
	def test_execute(self):
		# test 1: execute a command expecting a numeric output
		self.execute("snova --site {site} execute sparrow.db.get_database_size")
		self.assertEqual(self.returncode, 0)
		self.assertIsInstance(float(self.stdout), float)

		# test 2: execute a command expecting an errored output as local won't exist
		self.execute("snova --site {site} execute sparrow.local.site")
		self.assertEqual(self.returncode, 1)
		self.assertIsNotNone(self.stderr)

		# test 3: execute a command with kwargs
		# Note:
		# terminal command has been escaped to avoid .format string replacement
		# The returned value has quotes which have been trimmed for the test
		self.execute("""snova --site {site} execute sparrow.bold --kwargs '{{"text": "DocType"}}'""")
		self.assertEqual(self.returncode, 0)
		self.assertEqual(self.stdout[1:-1], sparrow.bold(text="DocType"))

	@unittest.skip
	def test_restore(self):
		# step 0: create a site to run the test on
		global_config = {
			"admin_password": sparrow.conf.admin_password,
			"root_login": sparrow.conf.root_login,
			"root_password": sparrow.conf.root_password,
			"db_type": sparrow.conf.db_type,
		}
		site_data = {"test_site": TEST_SITE, **global_config}
		for key, value in global_config.items():
			if value:
				self.execute(f"snova set-config {key} {value} -g")

		# test 1: snova restore from full backup
		self.execute("snova --site {test_site} backup --ignore-backup-conf", site_data)
		self.execute(
			"snova --site {test_site} execute sparrow.utils.backups.fetch_latest_backups",
			site_data,
		)
		site_data.update({"database": json.loads(self.stdout)["database"]})
		self.execute("snova --site {test_site} restore {database}", site_data)

		# test 2: restore from partial backup
		self.execute("snova --site {test_site} backup --exclude 'ToDo'", site_data)
		site_data.update({"kw": "\"{'partial':True}\""})
		self.execute(
			"snova --site {test_site} execute" " sparrow.utils.backups.fetch_latest_backups --kwargs {kw}",
			site_data,
		)
		site_data.update({"database": json.loads(self.stdout)["database"]})
		self.execute("snova --site {test_site} restore {database}", site_data)
		self.assertEqual(self.returncode, 1)

	def test_partial_restore(self):
		_now = now()
		for num in range(10):
			sparrow.get_doc(
				{
					"doctype": "ToDo",
					"date": add_to_date(_now, days=num),
					"description": sparrow.mock("paragraph"),
				}
			).insert()
		sparrow.db.commit()
		todo_count = sparrow.db.count("ToDo")

		# check if todos exist, create a partial backup and see if the state is the same after restore
		self.assertIsNot(todo_count, 0)
		self.execute("snova --site {site} backup --only 'ToDo'")
		db_path = fetch_latest_backups(partial=True)["database"]
		self.assertTrue("partial" in db_path)

		sparrow.db.sql_ddl("DROP TABLE IF EXISTS `tabToDo`")
		sparrow.db.commit()

		self.execute("snova --site {site} partial-restore {path}", {"path": db_path})
		self.assertEqual(self.returncode, 0)
		self.assertEqual(sparrow.db.count("ToDo"), todo_count)

	def test_recorder(self):
		sparrow.recorder.stop()

		self.execute("snova --site {site} start-recording")
		sparrow.local.cache = {}
		self.assertEqual(sparrow.recorder.status(), True)

		self.execute("snova --site {site} stop-recording")
		sparrow.local.cache = {}
		self.assertEqual(sparrow.recorder.status(), False)

	@unittest.skip("Poorly written, relied on app name being absent in apps.txt")
	def test_remove_from_installed_apps(self):
		app = "test_remove_app"
		add_to_installed_apps(app)

		# check: confirm that add_to_installed_apps added the app in the default
		self.execute("snova --site {site} list-apps")
		self.assertIn(app, self.stdout)

		# test 1: remove app from installed_apps global default
		self.execute("snova --site {site} remove-from-installed-apps {app}", {"app": app})
		self.assertEqual(self.returncode, 0)
		self.execute("snova --site {site} list-apps")
		self.assertNotIn(app, self.stdout)

	def test_list_apps(self):
		# test 1: sanity check for command
		self.execute("snova --site all list-apps")
		self.assertIsNotNone(self.returncode)
		self.assertIsInstance(self.stdout or self.stderr, str)

		# test 2: bare functionality for single site
		self.execute("snova --site {site} list-apps")
		self.assertEqual(self.returncode, 0)
		list_apps = {_x.split(maxsplit=1)[0] for _x in self.stdout.split("\n")}
		doctype = sparrow.get_single("Installed Applications").installed_applications
		if doctype:
			installed_apps = {x.app_name for x in doctype}
		else:
			installed_apps = set(sparrow.get_installed_apps())
		self.assertSetEqual(list_apps, installed_apps)

		# test 3: parse json format
		self.execute("snova --site {site} list-apps --format json")
		self.assertEqual(self.returncode, 0)
		self.assertIsInstance(json.loads(self.stdout), dict)

		self.execute("snova --site {site} list-apps -f json")
		self.assertEqual(self.returncode, 0)
		self.assertIsInstance(json.loads(self.stdout), dict)

	def test_show_config(self):
		# test 1: sanity check for command
		self.execute("snova --site all show-config")
		self.assertEqual(self.returncode, 0)

		# test 2: test keys in table text
		self.execute(
			"snova --site {site} set-config test_key '{second_order}' --parse",
			{"second_order": json.dumps({"test_key": "test_value"})},
		)
		self.execute("snova --site {site} show-config")
		self.assertEqual(self.returncode, 0)
		self.assertIn("test_key.test_key", self.stdout.split())
		self.assertIn("test_value", self.stdout.split())

		# test 3: parse json format
		self.execute("snova --site all show-config --format json")
		self.assertEqual(self.returncode, 0)
		self.assertIsInstance(json.loads(self.stdout), dict)

		self.execute("snova --site {site} show-config --format json")
		self.assertIsInstance(json.loads(self.stdout), dict)

		self.execute("snova --site {site} show-config -f json")
		self.assertIsInstance(json.loads(self.stdout), dict)

	def test_get_bench_relative_path(self):
		bench_path = get_bench_path()
		test1_path = os.path.join(bench_path, "test1.txt")
		test2_path = os.path.join(bench_path, "sites", "test2.txt")

		with open(test1_path, "w+") as test1:
			test1.write("asdf")
		with open(test2_path, "w+") as test2:
			test2.write("asdf")

		self.assertTrue("test1.txt" in get_bench_relative_path("test1.txt"))
		self.assertTrue("sites/test2.txt" in get_bench_relative_path("test2.txt"))
		with self.assertRaises(SystemExit):
			get_bench_relative_path("test3.txt")

		os.remove(test1_path)
		os.remove(test2_path)

	def test_sparrow_site_env(self):
		os.putenv("sparrow_SITE", sparrow.local.site)
		self.execute("snova execute sparrow.ping")
		self.assertEqual(self.returncode, 0)
		self.assertIn("pong", self.stdout)

	def test_version(self):
		self.execute("snova version")
		self.assertEqual(self.returncode, 0)

		for output in ["legacy", "plain", "table", "json"]:
			self.execute(f"snova version -f {output}")
			self.assertEqual(self.returncode, 0)

		self.execute("snova version -f invalid")
		self.assertEqual(self.returncode, 2)

	def test_set_password(self):
		from sparrow.utils.password import check_password

		self.execute("snova --site {site} set-password Administrator test1")
		self.assertEqual(self.returncode, 0)
		self.assertEqual(check_password("Administrator", "test1"), "Administrator")

		self.execute("snova --site {site} set-admin-password test2")
		self.assertEqual(self.returncode, 0)
		self.assertEqual(check_password("Administrator", "test2"), "Administrator")

		# Reset it back to original password
		original_password = sparrow.conf.admin_password or "admin"
		self.execute("snova --site {site} set-admin-password %s" % original_password)
		self.assertEqual(self.returncode, 0)
		self.assertEqual(check_password("Administrator", original_password), "Administrator")

	@skipIf(
		not (
                sparrow.conf.root_password and sparrow.conf.admin_password and sparrow.conf.db_type == "mariadb"
		),
		"DB Root password and Admin password not set in config",
	)
	def test_bench_drop_site_should_archive_site(self):
		# TODO: Make this test postgres compatible
		site = TEST_SITE

		self.execute(
			f"snova new-site {site} --force --verbose "
			f"--admin-password {sparrow.conf.admin_password} "
			f"--mariadb-root-password {sparrow.conf.root_password} "
			f"--db-type {sparrow.conf.db_type or 'mariadb'} "
		)
		self.assertEqual(self.returncode, 0)

		self.execute(f"snova drop-site {site} --force --root-password {sparrow.conf.root_password}")
		self.assertEqual(self.returncode, 0)

		bench_path = get_bench_path()
		site_directory = os.path.join(bench_path, f"sites/{site}")
		self.assertFalse(os.path.exists(site_directory))
		archive_directory = os.path.join(bench_path, f"archived/sites/{site}")
		self.assertTrue(os.path.exists(archive_directory))

	@skipIf(
		not (
                sparrow.conf.root_password and sparrow.conf.admin_password and sparrow.conf.db_type == "mariadb"
		),
		"DB Root password and Admin password not set in config",
	)
	def test_force_install_app(self):
		if not os.path.exists(os.path.join(get_bench_path(), f"sites/{TEST_SITE}")):
			self.execute(
				f"snova new-site {TEST_SITE} --verbose "
				f"--admin-password {sparrow.conf.admin_password} "
				f"--mariadb-root-password {sparrow.conf.root_password} "
				f"--db-type {sparrow.conf.db_type or 'mariadb'} "
			)

		app_name = "sparrow"

		# set admin password in site_config as when sparrow force installs, we don't have the conf
		self.execute(f"snova --site {TEST_SITE} set-config admin_password {sparrow.conf.admin_password}")

		# try installing the sparrow_docs app again on test site
		self.execute(f"snova --site {TEST_SITE} install-app {app_name}")
		self.assertIn(f"{app_name} already installed", self.stdout)
		self.assertEqual(self.returncode, 0)

		# force install sparrow_docs app on the test site
		self.execute(f"snova --site {TEST_SITE} install-app {app_name} --force")
		self.assertIn(f"Installing {app_name}", self.stdout)
		self.assertEqual(self.returncode, 0)

	def test_set_global_conf(self):
		key = "answer"
		value = "42"
		self.execute(f"snova set-config {key} {value} -g")
		conf = sparrow.get_site_config()

		self.assertEqual(conf[key], value)


class TestBackups(BaseTestCommands):
	backup_map = {
		"includes": {
			"includes": [
				"ToDo",
				"Note",
			]
		},
		"excludes": {"excludes": ["Activity Log", "Access Log", "Error Log"]},
	}
	home = os.path.expanduser("~")
	site_backup_path = sparrow.utils.get_site_path("private", "backups")

	def setUp(self):
		self.files_to_trash = []

	def tearDown(self):
		if self._testMethodName == "test_backup":
			for file in self.files_to_trash:
				os.remove(file)
				try:
					os.rmdir(os.path.dirname(file))
				except OSError:
					pass

	def test_backup_no_options(self):
		"""Take a backup without any options"""
		before_backup = fetch_latest_backups(partial=True)
		self.execute("snova --site {site} backup")
		after_backup = fetch_latest_backups(partial=True)

		self.assertEqual(self.returncode, 0)
		self.assertIn("successfully completed", self.stdout)
		self.assertNotEqual(before_backup["database"], after_backup["database"])

	def test_backup_fails_with_exit_code(self):
		"""Provide incorrect options to check if exit code is 1"""
		odb = BackupGenerator(
			sparrow.conf.db_name,
			sparrow.conf.db_name,
            sparrow.conf.db_password + "INCORRECT PASSWORD",
			db_host=sparrow.db.host,
			db_port=sparrow.db.port,
			db_type=sparrow.conf.db_type,
		)
		with self.assertRaises(Exception):
			odb.take_dump()

	def test_backup_with_files(self):
		"""Take a backup with files (--with-files)"""
		before_backup = fetch_latest_backups()
		self.execute("snova --site {site} backup --with-files")
		after_backup = fetch_latest_backups()

		self.assertEqual(self.returncode, 0)
		self.assertIn("successfully completed", self.stdout)
		self.assertIn("with files", self.stdout)
		self.assertNotEqual(before_backup, after_backup)
		self.assertIsNotNone(after_backup["public"])
		self.assertIsNotNone(after_backup["private"])

	@run_only_if(db_type_is.MARIADB)
	def test_clear_log_table(self):
		d = sparrow.get_doc(doctype="Error Log", title="Something").insert()
		d.db_set("modified", "2010-01-01", update_modified=False)
		sparrow.db.commit()

		tables_before = sparrow.db.get_tables(cached=False)

		self.execute("snova --site {site} clear-log-table --days=30 --doctype='Error Log'")
		self.assertEqual(self.returncode, 0)
		sparrow.db.commit()

		self.assertFalse(sparrow.db.exists("Error Log", d.name))
		tables_after = sparrow.db.get_tables(cached=False)

		self.assertEqual(set(tables_before), set(tables_after))

	def test_backup_with_custom_path(self):
		"""Backup to a custom path (--backup-path)"""
		backup_path = os.path.join(self.home, "backups")
		self.execute(
			"snova --site {site} backup --backup-path {backup_path}", {"backup_path": backup_path}
		)

		self.assertEqual(self.returncode, 0)
		self.assertTrue(os.path.exists(backup_path))
		self.assertGreaterEqual(len(os.listdir(backup_path)), 2)

	def test_backup_with_different_file_paths(self):
		"""Backup with different file paths (--backup-path-db, --backup-path-files, --backup-path-private-files, --backup-path-conf)"""
		kwargs = {
			key: os.path.join(self.home, key, value)
			for key, value in {
				"db_path": "database.sql.gz",
				"files_path": "public.tar",
				"private_path": "private.tar",
				"conf_path": "config.json",
			}.items()
		}

		self.execute(
			"""snova
			--site {site} backup --with-files
			--backup-path-db {db_path}
			--backup-path-files {files_path}
			--backup-path-private-files {private_path}
			--backup-path-conf {conf_path}""",
			kwargs,
		)

		self.assertEqual(self.returncode, 0)
		for path in kwargs.values():
			self.assertTrue(os.path.exists(path))

	def test_backup_compress_files(self):
		"""Take a compressed backup (--compress)"""
		self.execute("snova --site {site} backup --with-files --compress")
		self.assertEqual(self.returncode, 0)
		compressed_files = glob(f"{self.site_backup_path}/*.tgz")
		self.assertGreater(len(compressed_files), 0)

	def test_backup_verbose(self):
		"""Take a verbose backup (--verbose)"""
		self.execute("snova --site {site} backup --verbose")
		self.assertEqual(self.returncode, 0)

	def test_backup_only_specific_doctypes(self):
		"""Take a backup with (include) backup options set in the site config `sparrow.conf.backup.includes`"""
		self.execute(
			"snova --site {site} set-config backup '{includes}' --parse",
			{"includes": json.dumps(self.backup_map["includes"])},
		)
		self.execute("snova --site {site} backup --verbose")
		self.assertEqual(self.returncode, 0)
		database = fetch_latest_backups(partial=True)["database"]
		self.assertEqual([], missing_in_backup(self.backup_map["includes"]["includes"], database))

	def test_backup_excluding_specific_doctypes(self):
		"""Take a backup with (exclude) backup options set (`sparrow.conf.backup.excludes`, `--exclude`)"""
		# test 1: take a backup with sparrow.conf.backup.excludes
		self.execute(
			"snova --site {site} set-config backup '{excludes}' --parse",
			{"excludes": json.dumps(self.backup_map["excludes"])},
		)
		self.execute("snova --site {site} backup --verbose")
		self.assertEqual(self.returncode, 0)
		database = fetch_latest_backups(partial=True)["database"]
		self.assertFalse(exists_in_backup(self.backup_map["excludes"]["excludes"], database))
		self.assertEqual([], missing_in_backup(self.backup_map["includes"]["includes"], database))

		# test 2: take a backup with --exclude
		self.execute(
			"snova --site {site} backup --exclude '{exclude}'",
			{"exclude": ",".join(self.backup_map["excludes"]["excludes"])},
		)
		self.assertEqual(self.returncode, 0)
		database = fetch_latest_backups(partial=True)["database"]
		self.assertFalse(exists_in_backup(self.backup_map["excludes"]["excludes"], database))

	def test_selective_backup_priority_resolution(self):
		"""Take a backup with conflicting backup options set (`sparrow.conf.excludes`, `--include`)"""
		self.execute(
			"snova --site {site} backup --include '{include}'",
			{"include": ",".join(self.backup_map["includes"]["includes"])},
		)
		self.assertEqual(self.returncode, 0)
		database = fetch_latest_backups(partial=True)["database"]
		self.assertEqual([], missing_in_backup(self.backup_map["includes"]["includes"], database))

	def test_dont_backup_conf(self):
		"""Take a backup ignoring sparrow.conf.backup settings (with --ignore-backup-conf option)"""
		self.execute("snova --site {site} backup --ignore-backup-conf")
		self.assertEqual(self.returncode, 0)
		database = fetch_latest_backups()["database"]
		self.assertEqual([], missing_in_backup(self.backup_map["excludes"]["excludes"], database))


class TestRemoveApp(sparrowTestCase):
	def test_delete_modules(self):
		from sparrow.installer import (
			_delete_doctypes,
			_delete_modules,
			_get_module_linked_doctype_field_map,
		)

		test_module = sparrow.new_doc("Module Def")

		test_module.update({"module_name": "RemoveThis", "app_name": "sparrow"})
		test_module.save()

		module_def_linked_doctype = sparrow.get_doc(
			{
				"doctype": "DocType",
				"name": "Doctype linked with module def",
				"module": "RemoveThis",
				"custom": 1,
				"fields": [
					{"label": "Modulen't", "fieldname": "notmodule", "fieldtype": "Link", "options": "Module Def"}
				],
			}
		).insert()

		doctype_to_link_field_map = _get_module_linked_doctype_field_map()

		self.assertIn("Report", doctype_to_link_field_map)
		self.assertIn(module_def_linked_doctype.name, doctype_to_link_field_map)
		self.assertEqual(doctype_to_link_field_map[module_def_linked_doctype.name], "notmodule")
		self.assertNotIn("DocType", doctype_to_link_field_map)

		doctypes_to_delete = _delete_modules([test_module.module_name], dry_run=False)
		self.assertEqual(len(doctypes_to_delete), 1)

		_delete_doctypes(doctypes_to_delete, dry_run=False)
		self.assertFalse(sparrow.db.exists("Module Def", test_module.module_name))
		self.assertFalse(sparrow.db.exists("DocType", module_def_linked_doctype.name))

	def test_dry_run(self):
		"""Check if dry run in not destructive."""

		# nothing to assert, if this fails rest of the test suite will crumble.
		remove_app("sparrow", dry_run=True, yes=True, no_backup=True)


class TestSiteMigration(BaseTestCommands):
	def test_migrate_cli(self):
		with cli(sparrow.commands.site.migrate) as result:
			self.assertTrue(TEST_SITE in result.stdout)
			self.assertEqual(result.exit_code, 0)
			self.assertEqual(result.exception, None)


class TestAddNewUser(BaseTestCommands):
	def test_create_user(self):
		self.execute(
			"snova --site {site} add-user test@gmail.com --first-name test --last-name test --password 123 --user-type 'System User' --add-role 'Accounts User' --add-role 'Sales User'"
		)
		sparrow.db.rollback()
		self.assertEqual(self.returncode, 0)
		user = sparrow.get_doc("User", "test@gmail.com")
		roles = {r.role for r in user.roles}
		self.assertEqual({"Accounts User", "Sales User"}, roles)


class TestBenchBuild(BaseTestCommands):
	def test_build_assets_size_check(self):
		with cli(sparrow.commands.utils.build, "--force --production") as result:
			self.assertEqual(result.exit_code, 0)
			self.assertEqual(result.exception, None)

		CURRENT_SIZE = 3.5  # MB
		JS_ASSET_THRESHOLD = 0.1

		hooks = sparrow.get_hooks()
		default_bundle = hooks["app_include_js"]

		default_bundle_size = 0.0

		for chunk in default_bundle:
			abs_path = Path.cwd() / sparrow.local.sites_path / bundled_asset(chunk)[1:]
			default_bundle_size += abs_path.stat().st_size

		self.assertLessEqual(
			default_bundle_size / (1024 * 1024),
			CURRENT_SIZE * (1 + JS_ASSET_THRESHOLD),
			f"Default JS bundle size increased by {JS_ASSET_THRESHOLD:.2%} or more",
		)


class TestCommandUtils(sparrowTestCase):
	def test_bench_helper(self):
		from sparrow.utils.snova_helper import get_app_groups

		app_groups = get_app_groups()
		self.assertIn("sparrow", app_groups)
		self.assertIsInstance(app_groups["sparrow"], click.Group)


class TestDBCli(BaseTestCommands):
	@timeout(10)
	def test_db_cli(self):
		self.execute("snova --site {site} db-console", kwargs={"cmd_input": rb"\q"})
		self.assertEqual(self.returncode, 0)


class TestSchedulerCLI(BaseTestCommands):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.is_scheduler_active = not is_scheduler_inactive()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		if cls.is_scheduler_active:
			enable_scheduler()

	def test_scheduler_status(self):
		self.execute("snova --site {site} scheduler status")
		self.assertEqual(self.returncode, 0)
		self.assertRegex(self.stdout, r"Scheduler is (disabled|enabled) for site .*")

		self.execute("snova --site {site} scheduler status -f json")
		parsed_output = sparrow.parse_json(self.stdout)
		self.assertEqual(self.returncode, 0)
		self.assertIsInstance(parsed_output, dict)
		self.assertIn("status", parsed_output)
		self.assertIn("site", parsed_output)

	def test_scheduler_enable_disable(self):
		self.execute("snova --site {site} scheduler disable")
		self.assertEqual(self.returncode, 0)
		self.assertRegex(self.stdout, r"Scheduler is disabled for site .*")

		self.execute("snova --site {site} scheduler enable")
		self.assertEqual(self.returncode, 0)
		self.assertRegex(self.stdout, r"Scheduler is enabled for site .*")

	def test_scheduler_pause_resume(self):
		self.execute("snova --site {site} scheduler pause")
		self.assertEqual(self.returncode, 0)
		self.assertRegex(self.stdout, r"Scheduler is paused for site .*")

		self.execute("snova --site {site} scheduler resume")
		self.assertEqual(self.returncode, 0)
		self.assertRegex(self.stdout, r"Scheduler is resumed for site .*")
