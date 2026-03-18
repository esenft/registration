# Rather than follow the order of the previous scripts, this file starts by creating the user interface and then goes into the different functions involved
# The user is presented with the interface in the command line and can select which action they want to perform

"""Unified executable script for the registration application."""

import sqlite3
from typing import Callable

import create_user
import update_user
from create_database_and_table import create_database_and_table
from create_user import validate_username
from db_connection import create_sqlite_connection
from delete_user import delete_user_by_username
from populate_users import TOTAL_USERS, insert_synthetic_users
from read_users import HEADERS, fetch_all_users, normalize_cell
from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table


console = Console()


def show_info(message: str) -> None:
	"""Display a formatted info panel."""
	console.print(Panel(message, border_style="blue"))


def show_warning(message: str) -> None:
	"""Display a formatted warning panel."""
	console.print(Panel(message, border_style="yellow"))


def show_error(message: str) -> None:
	"""Display a formatted error panel."""
	console.print(Panel(message, border_style="red"))


def print_menu() -> None:
	"""Render the main menu options."""
	console.print(
		Panel.fit(
			"\n".join(
				[
					"[bold cyan]1[/bold cyan]. Initialize database and users table",
					"[bold cyan]2[/bold cyan]. Create a new user",
					"[bold cyan]3[/bold cyan]. Read/display one user",
					"[bold cyan]4[/bold cyan]. Read/display all users",
					"[bold cyan]5[/bold cyan]. Update an existing user",
					"[bold cyan]6[/bold cyan]. Delete a user",
					"[bold cyan]7[/bold cyan]. Populate synthetic users",
					"[bold cyan]8[/bold cyan]. Exit",
				]
			),
			title="[bold green]Registration App Menu[/bold green]",
			border_style="green",
		)
	)


def render_users_table(rows: list[tuple], title: str) -> None:
	"""Render user rows in a Rich table."""
	if not rows:
		show_warning("No users found.")
		return

	table = Table(title=title, header_style="bold cyan")
	for header in HEADERS:
		table.add_column(header)

	for row in rows:
		table.add_row(*[normalize_cell(value) for value in row])

	console.print(table)
	show_info(f"Total users shown: {len(rows)}")


def setup_database() -> None:
	"""Initialize database and users table."""
	create_database_and_table()


def create_new_user() -> None:
	"""Run interactive user creation flow."""
	create_user.main()


def read_one_user() -> None:
	"""Prompt for username and display one matching user."""
	try:
		username_input = Prompt.ask("Enter username to display")
		username = validate_username(username_input)
	except ValueError as exc:
		show_error(f"Invalid input: {exc}")
		return

	connection = None

	try:
		connection = create_sqlite_connection()
		cursor = connection.cursor()
		cursor.execute(
			"""
			SELECT id, username, email, password, city, company, job_title
			FROM users
			WHERE username = ?
			""",
			(username,),
		)
		row = cursor.fetchone()
		if row is None:
			show_warning(f"User '{username}' not found.")
			return

		render_users_table([row], f"User: {username}")
	except sqlite3.Error as exc:
		message = str(exc)
		if "no such table" in message.lower():
			show_error("Table 'users' was not found. Run initialization first.")
		else:
			show_error(f"Failed to read user: {exc}")
	finally:
		if connection is not None:
			connection.close()
			console.print("SQLite connection closed.")


def read_all_users() -> None:
	"""Display all users from the users table."""
	users = fetch_all_users()
	render_users_table(users, "All Users")


def update_existing_user() -> None:
	"""Run interactive update flow for an existing user."""
	update_user.update_user()


def delete_existing_user() -> None:
	"""Prompt for username and delete user."""
	username = Prompt.ask("Enter username to delete")
	delete_user_by_username(username)


def populate_synthetic_users() -> None:
	"""Insert synthetic users using Faker-based population logic."""
	target_count = IntPrompt.ask(
		"How many synthetic users should be inserted",
		default=TOTAL_USERS,
	)

	if target_count <= 0:
		show_error("Please enter a positive integer.")
		return

	inserted = insert_synthetic_users(target_count)
	show_info(f"Successfully inserted {inserted} synthetic users.")


def run_action(action: Callable[[], None], action_name: str) -> None:
	"""Execute a menu action with consistent top-level error handling."""
	try:
		action()
	except RuntimeError as exc:
		show_error(str(exc))
	except ValueError as exc:
		show_error(f"Invalid input: {exc}")
	except sqlite3.Error as exc:
		show_error(f"Database error during {action_name.lower()}: {exc}")
	except KeyboardInterrupt:
		show_warning("Operation cancelled.")
	except Exception as exc:
		show_error(f"Unexpected error during {action_name.lower()}: {exc}")


def run_application() -> None:
	"""Run the unified interactive application loop."""
	actions: dict[str, tuple[str, Callable[[], None]]] = {
		"1": ("Initialize Database", setup_database),
		"2": ("Create User", create_new_user),
		"3": ("Read One User", read_one_user),
		"4": ("Read All Users", read_all_users),
		"5": ("Update User", update_existing_user),
		"6": ("Delete User", delete_existing_user),
		"7": ("Populate Synthetic Users", populate_synthetic_users),
	}

	console.print(
		Panel.fit(
			"Welcome to the unified Registration application.",
			title="[bold green]Start[/bold green]",
			border_style="green",
		)
	)

	while True:
		print_menu()
		try:
			choice = Prompt.ask("Choose an option", default="8").strip()
		except (KeyboardInterrupt, EOFError):
			console.print("\nExiting application.")
			break

		if choice == "8":
			console.print(Panel.fit("Goodbye.", border_style="green"))
			break

		selected = actions.get(choice)
		if selected is None:
			show_error("Invalid option. Please enter a number from 1 to 8.")
			continue

		action_name, action = selected
		run_action(action, action_name)


if __name__ == "__main__":
	run_application()
