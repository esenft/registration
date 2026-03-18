"""Delete a user record from the users table by username."""

import sqlite3

from create_user import validate_username
from db_connection import create_sqlite_connection


def delete_user_by_username(username: str) -> None:
	"""Delete a user identified by username."""
	connection = None

	try:
		sanitized_username = validate_username(username)
		connection = create_sqlite_connection()
		cursor = connection.cursor()

		cursor.execute("SELECT id FROM users WHERE username = ?", (sanitized_username,))
		if cursor.fetchone() is None:
			print(f"User '{sanitized_username}' not found. No records were deleted.")
			return

		cursor.execute("DELETE FROM users WHERE username = ?", (sanitized_username,))
		connection.commit()
		print(f"User '{sanitized_username}' deleted successfully.")
	except sqlite3.Error as exc:
		message = str(exc)
		if "no such table" in message.lower():
			print("Table 'users' was not found. Run create_database_and_table.py first.")
		else:
			print(f"Failed to delete user: {exc}")
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


def main() -> None:
	"""Prompt for username and delete matching user record."""
	try:
		username = input("Enter username to delete: ")
		delete_user_by_username(username)
	except ValueError as exc:
		print(f"Invalid input: {exc}")
	except KeyboardInterrupt:
		print("\nOperation cancelled.")


if __name__ == "__main__":
	main()
