# Copyright (c) 2015, Sparrownova Technologies and Contributors
# License: MIT. See LICENSE

# Database Module
# --------------------

from sparrow.database.database import savepoint


def setup_database(force, source_sql=None, verbose=None, no_mariadb_socket=False):
	import sparrow

	if sparrow.conf.db_type == "postgres":
		import sparrow.database.postgres.setup_db

		return sparrow.database.postgres.setup_db.setup_database(force, source_sql, verbose)
	else:
		import sparrow.database.mariadb.setup_db

		return sparrow.database.mariadb.setup_db.setup_database(
			force, source_sql, verbose, no_mariadb_socket=no_mariadb_socket
		)


def drop_user_and_database(db_name, root_login=None, root_password=None):
	import sparrow

	if sparrow.conf.db_type == "postgres":
		import sparrow.database.postgres.setup_db

		return sparrow.database.postgres.setup_db.drop_user_and_database(
			db_name, root_login, root_password
		)
	else:
		import sparrow.database.mariadb.setup_db

		return sparrow.database.mariadb.setup_db.drop_user_and_database(
			db_name, root_login, root_password
		)


def get_db(host=None, user=None, password=None, port=None):
	import sparrow

	if sparrow.conf.db_type == "postgres":
		import sparrow.database.postgres.database

		return sparrow.database.postgres.database.PostgresDatabase(host, user, password, port=port)
	else:
		import sparrow.database.mariadb.database

		return sparrow.database.mariadb.database.MariaDBDatabase(host, user, password, port=port)


def setup_help_database(help_db_name):
	import sparrow

	if sparrow.conf.db_type == "postgres":
		import sparrow.database.postgres.setup_db

		return sparrow.database.postgres.setup_db.setup_help_database(help_db_name)
	else:
		import sparrow.database.mariadb.setup_db

		return sparrow.database.mariadb.setup_db.setup_help_database(help_db_name)
