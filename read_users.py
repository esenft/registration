# This script allows users to view all of the records inside the database
# It connects to the SQLite database, retrieves all user records from the users table, and displays them in a formatted table in the command line

"""Read and display all user records from the users table."""

import sqlite3

from db_connection import create_sqlite_connection


HEADERS = ["id", "username", "email", "password", "city", "company", "job_title"]
MAX_COLUMN_WIDTH = 40


def fetch_all_users() -> list[tuple]:
	"""Fetch every user row from the users table."""
	connection = None

	try:
		connection = create_sqlite_connection()
		cursor = connection.cursor()
		cursor.execute(
			"""
			SELECT id, username, email, password, city, company, job_title
			FROM users
			ORDER BY id ASC
			"""
		)
		return cursor.fetchall()
	except sqlite3.Error as exc:
		message = str(exc)
		if "no such table" in message.lower():
			raise RuntimeError(
				"Table 'users' was not found. Run create_database_and_table.py first."
			) from exc
		raise RuntimeError(f"Failed to read users: {exc}") from exc
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


def normalize_cell(value: object) -> str:
	"""Convert DB values to readable strings for table rendering."""
	if value is None:
		return ""

	text = str(value)
	if len(text) > MAX_COLUMN_WIDTH:
		return text[: MAX_COLUMN_WIDTH - 3] + "..."
	return text


def render_table(rows: list[tuple]) -> None:
	"""Print users in a formatted command-line table."""
	if not rows:
		print("No users found in table 'users'.")
		return

	normalized_rows = [[normalize_cell(value) for value in row] for row in rows]
	column_widths = [len(header) for header in HEADERS]

	for row in normalized_rows:
		for index, value in enumerate(row):
			column_widths[index] = max(column_widths[index], len(value))

	separator = "+-" + "-+-".join("-" * width for width in column_widths) + "-+"
	header_line = "| " + " | ".join(
		header.ljust(column_widths[index]) for index, header in enumerate(HEADERS)
	) + " |"

	print(separator)
	print(header_line)
	print(separator)

	for row in normalized_rows:
		row_line = "| " + " | ".join(
			value.ljust(column_widths[index]) for index, value in enumerate(row)
		) + " |"
		print(row_line)

	print(separator)
	print(f"Total users: {len(rows)}")


def main() -> None:
	"""Load all users and display them as a table."""
	try:
		users = fetch_all_users()
		render_table(users)
	except RuntimeError as exc:
		print(exc)


if __name__ == "__main__":
	main()
