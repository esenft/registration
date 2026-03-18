# This script uses the Faker library to generate synthetic user data and insert it into the users table in batches of 250
# It handles potential integrity errors due to duplicate usernames or emails by using INSERT OR IGNORE and retrying until the desired number of unique users is inserted
# The script also ensures all usernames are unique, and that the database schema applies 

"""Generate and insert synthetic users into the users table."""

import sqlite3

from faker import Faker

from create_user import (
	hash_password,
	validate_email,
	validate_text_field,
	validate_username,
)
from db_connection import create_sqlite_connection


TOTAL_USERS = 1_000
BATCH_SIZE = 250
MAX_EMPTY_BATCHES = 20


def generate_synthetic_user(
	fake: Faker,
	password_hash: str,
) -> tuple[str, str, str, str, str, str]:
	"""Generate one synthetic user record that satisfies validation rules."""
	while True:
		try:
			username_raw = (
				f"{fake.user_name()}_{fake.unique.random_int(min=100000, max=999999)}"
			)
			username = validate_username(username_raw[:30])

			email_raw = f"{fake.unique.uuid4()}@{fake.free_email_domain()}"
			email = validate_email(email_raw)

			city = validate_text_field(fake.city(), "City")
			company = validate_text_field(fake.company(), "Company")
			job_title = validate_text_field(fake.job(), "Job title")

			return username, email, password_hash, city, company, job_title
		except ValueError:
			# Regenerate values until they satisfy validation rules.
			continue


def insert_synthetic_users(total_users: int) -> int:
	"""Insert exactly total_users new synthetic users and return inserted count."""
	connection = None

	try:
		fake = Faker()
		password_hash = hash_password("Password123")
		inserted_total = 0
		empty_batch_count = 0

		connection = create_sqlite_connection()
		cursor = connection.cursor()

		while inserted_total < total_users:
			remaining = total_users - inserted_total
			current_batch_size = min(BATCH_SIZE, remaining)
			batch = [
				generate_synthetic_user(fake, password_hash)
				for _ in range(current_batch_size)
			]

			cursor.executemany(
				"""
				INSERT OR IGNORE INTO users (username, email, password, city, company, job_title)
				VALUES (?, ?, ?, ?, ?, ?)
				""",
				batch,
			)
			connection.commit()

			inserted_in_batch = max(cursor.rowcount, 0)
			inserted_total += inserted_in_batch

			if inserted_in_batch == 0:
				empty_batch_count += 1
				if empty_batch_count >= MAX_EMPTY_BATCHES:
					raise RuntimeError(
						"Unable to insert new unique users after multiple retries."
					)
			else:
				empty_batch_count = 0

		return inserted_total
	except sqlite3.Error as exc:
		message = str(exc)
		if "no such table" in message.lower():
			raise RuntimeError(
				"Table 'users' was not found. Run create_database_and_table.py first."
			) from exc
		raise RuntimeError(f"Failed to insert synthetic users: {exc}") from exc
	finally:
		if connection is not None:
			connection.close()
			print("SQLite connection closed.")


def main() -> None:
	"""Generate and insert 1000 synthetic users into users.db."""
	try:
		inserted = insert_synthetic_users(TOTAL_USERS)
		print(f"Successfully inserted {inserted} synthetic users into users.db.")
	except RuntimeError as exc:
		print(exc)
	except KeyboardInterrupt:
		print("\nOperation cancelled.")


if __name__ == "__main__":
	main()
