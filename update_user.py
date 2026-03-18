"""Update an existing user's email or password in the users table."""

import sqlite3

from create_user import (
	hash_password,
	prompt_password,
	validate_email,
	validate_password,
	validate_username,
)
from db_connection import create_sqlite_connection


def prompt_until_valid(prompt_text: str, validator, secret: bool = False) -> str:
	"""Prompt until valid input is provided."""
	while True:
		user_input = prompt_password(prompt_text) if secret else input(prompt_text)
		try:
			return validator(user_input)
		except ValueError as exc:
			print(f"Invalid input: {exc}")


def prompt_update_field() -> str:
	"""Prompt for which field should be updated."""
	print("Select field to update:")
	print("1. Email")
	print("2. Password")

	while True:
		choice = input("Enter choice (1/2 or email/password): ").strip().lower()
		if choice in {"1", "email"}:
			return "email"
		if choice in {"2", "password"}:
			return "password"
		print("Invalid choice. Please enter 1, 2, email, or password.")


def update_user_email(cursor: sqlite3.Cursor, username: str, new_email: str) -> None:
	"""Update a user's email by username."""
	cursor.execute(
		"""
		UPDATE users
		SET email = ?
		WHERE username = ?
		""",
		(new_email, username),
	)


def update_user_password(
	cursor: sqlite3.Cursor,
	username: str,
	hashed_password: str,
) -> None:
	"""Update a user's password hash by username."""
	cursor.execute(
		"""
		UPDATE users
		SET password = ?
		WHERE username = ?
		""",
		(hashed_password, username),
	)


def update_user() -> None:
	"""Collect inputs, validate, and update selected user field."""
	connection = None

	try:
		username = prompt_until_valid("Enter existing username: ", validate_username)
		field_to_update = prompt_update_field()

		connection = create_sqlite_connection()
		cursor = connection.cursor()

		cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
		if cursor.fetchone() is None:
			raise RuntimeError(f"User '{username}' not found.")

		if field_to_update == "email":
			new_email = prompt_until_valid("Enter new email: ", validate_email)
			update_user_email(cursor, username, new_email)
			connection.commit()

			cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
			updated_email = cursor.fetchone()[0]
			print(f"Email updated successfully for '{username}'.")
			print(f"Current email: {updated_email}")
		else:
			while True:
				new_password = prompt_until_valid(
					"Enter new password: ",
					validate_password,
					secret=True,
				)
				confirm_password = prompt_password("Confirm new password: ")
				if new_password != confirm_password:
					print("Passwords do not match. Please try again.")
					continue
				break

			hashed_password = hash_password(new_password)
			update_user_password(cursor, username, hashed_password)
			connection.commit()
			print(f"Password updated successfully for '{username}'.")

	except sqlite3.IntegrityError as exc:
		message = str(exc).lower()
		if "email" in message:
			print("Update failed: that email is already in use.")
		else:
			print(f"Update failed: {exc}")
	except sqlite3.Error as exc:
		print(f"Database error: {exc}")
	except RuntimeError as exc:
		print(exc)
	except KeyboardInterrupt:
		print("\nOperation cancelled.")
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


if __name__ == "__main__":
	update_user()
