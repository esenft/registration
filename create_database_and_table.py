# I chose to use SQLite over SQL for simplicity and ease of setup.
# This script creates the SQLite database file and the users table if they don't already exist
# The database schema is defined, to include the auto-incrementing ID for the primary key
# The functions read the config from the db.yaml file to get the database name and falls back to users.db if not specified

"""Create users.db and ensure the users table exists."""

import sqlite3

from db_connection import create_sqlite_connection, load_db_config


CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username TEXT NOT NULL UNIQUE,
	email TEXT NOT NULL UNIQUE,
	password TEXT,
	city TEXT,
	company TEXT,
	job_title TEXT
);
"""


def create_database_and_table() -> None:
	"""Create the SQLite database and users table from configuration."""
	connection = None

	try:
		config = load_db_config()
		database_name = str(config.get("database", "users.db"))

		connection = create_sqlite_connection()
		cursor = connection.cursor()
		cursor.execute(CREATE_USERS_TABLE_SQL)
		connection.commit()

		print(
			f"Database '{database_name}' initialized successfully with table 'users'."
		)
	except sqlite3.Error as exc:
		raise RuntimeError(f"Failed to create database/table: {exc}") from exc
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


if __name__ == "__main__":
	create_database_and_table()
