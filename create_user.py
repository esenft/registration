# This file adds users to the database we created
# The user is prompted to enter their username, email, password, city, company, and job title
# Error handling is included to validate the inputs and ensure the username and email are unique
# The password is hashed using PBKDF2-HMAC with a random salt for security
# The password is also rejected if it is not secure enough (with lowercase and uppercase letters, numbers, and at least 8 characters)


"""Create and insert a user record into the users table."""

from getpass import getpass
import hashlib
import os
import re
import sqlite3

from db_connection import create_sqlite_connection


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def validate_username(username: str) -> str:
	"""Validate username format and return a sanitized value."""
	value = username.strip()
	if not value:
		raise ValueError("Username is required.")
	if not USERNAME_PATTERN.fullmatch(value):
		raise ValueError(
			"Username must be 3-30 characters and use only letters, numbers, ., _, or -."
		)
	return value


def validate_email(email: str) -> str:
	"""Validate email format and return a normalized value."""
	value = email.strip().lower()
	if not value:
		raise ValueError("Email is required.")
	if not EMAIL_PATTERN.fullmatch(value):
		raise ValueError("Enter a valid email address.")
	return value


def validate_password(password: str) -> str:
	"""Validate password strength."""
	if not password:
		raise ValueError("Password is required.")
	if len(password) < 8:
		raise ValueError("Password must be at least 8 characters long.")
	if not any(char.isupper() for char in password):
		raise ValueError("Password must include at least one uppercase letter.")
	if not any(char.islower() for char in password):
		raise ValueError("Password must include at least one lowercase letter.")
	if not any(char.isdigit() for char in password):
		raise ValueError("Password must include at least one number.")
	return password


def validate_text_field(value: str, field_name: str, max_length: int = 100) -> str:
	"""Validate generic text fields (city, company, job title)."""
	sanitized = value.strip()
	if not sanitized:
		raise ValueError(f"{field_name} is required.")
	if len(sanitized) > max_length:
		raise ValueError(f"{field_name} must be {max_length} characters or fewer.")
	return sanitized


def hash_password(password: str, iterations: int = 200_000) -> str:
	"""Hash password with PBKDF2-HMAC and a random salt."""
	salt = os.urandom(16)
	digest = hashlib.pbkdf2_hmac(
		"sha256",
		password.encode("utf-8"),
		salt,
		iterations,
	)
	return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def prompt_password(prompt_text: str) -> str:
	"""Prompt for password input with hidden-entry fallback support."""
	print("Password input is hidden while typing. Type it and press Enter.")
	try:
		return getpass(prompt_text)
	except (EOFError, KeyboardInterrupt):
		raise
	except Exception:
		print("Hidden password input is not supported in this terminal.")
		print("Password will be visible while you type.")
		return input(prompt_text)


def prompt_until_valid(prompt_text: str, validator, secret: bool = False) -> str:
	"""Prompt until valid input is provided."""
	while True:
		user_input = prompt_password(prompt_text) if secret else input(prompt_text)
		try:
			return validator(user_input)
		except ValueError as exc:
			print(f"Invalid input: {exc}")


def collect_user_input() -> tuple[str, str, str, str, str, str]:
	"""Collect all user fields interactively."""
	username = prompt_until_valid("Username: ", validate_username)
	email = prompt_until_valid("Email: ", validate_email)
	password = prompt_until_valid("Password: ", validate_password, secret=True)
	city = prompt_until_valid("City: ", lambda value: validate_text_field(value, "City"))
	company = prompt_until_valid(
		"Company: ", lambda value: validate_text_field(value, "Company")
	)
	job_title = prompt_until_valid(
		"Job Title: ", lambda value: validate_text_field(value, "Job title")
	)

	hashed_password = hash_password(password)
	return username, email, hashed_password, city, company, job_title


def insert_user(
	username: str,
	email: str,
	hashed_password: str,
	city: str,
	company: str,
	job_title: str,
) -> None:
	"""Insert a user record into the users table."""
	connection = None

	try:
		connection = create_sqlite_connection()
		cursor = connection.cursor()
		cursor.execute(
			"""
			INSERT INTO users (username, email, password, city, company, job_title)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(username, email, hashed_password, city, company, job_title),
		)
		connection.commit()
		print(f"User '{username}' inserted successfully.")
	except sqlite3.IntegrityError as exc:
		message = str(exc).lower()
		if "username" in message:
			raise RuntimeError("A user with this username already exists.") from exc
		if "email" in message:
			raise RuntimeError("A user with this email already exists.") from exc
		raise RuntimeError(f"Failed to insert user: {exc}") from exc
	except sqlite3.Error as exc:
		raise RuntimeError(f"Failed to insert user: {exc}") from exc
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


def main() -> None:
	"""Prompt for user data and insert a new record."""
	try:
		user_data = collect_user_input()
		insert_user(*user_data)
	except RuntimeError as exc:
		print(exc)
	except KeyboardInterrupt:
		print("\nOperation cancelled.")


if __name__ == "__main__":
	main()
