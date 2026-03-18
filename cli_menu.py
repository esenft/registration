# This code first creates a Rich console instance for styled outputs.
# The menu displayed has options 1 through 6 for each CRUD operation and exit.
# It waits for the user input in a loop.
# It maps the selected optoin to a function and executes it. 
# If the user selects "Exit", it will break the loop and end the program.

"""Rich-powered CLI menu for user registration CRUD operations."""

import sqlite3

import create_user
import update_user
from create_user import validate_username
from db_connection import create_sqlite_connection
from delete_user import delete_user_by_username
from read_users import HEADERS, fetch_all_users, normalize_cell
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


console = Console()


def print_menu() -> None:
	"""Render the main menu panel."""
	console.print(
		Panel.fit(
			"\n".join(
				[
					"[bold cyan]1[/bold cyan]. Create a new user",
					"[bold cyan]2[/bold cyan]. Read/display one user",
					"[bold cyan]3[/bold cyan]. Read/display all users",
					"[bold cyan]4[/bold cyan]. Update an existing user",
					"[bold cyan]5[/bold cyan]. Delete a user",
					"[bold cyan]6[/bold cyan]. Exit",
				]
			),
			title="[bold green]User Management Menu[/bold green]",
			border_style="green",
		)
	)


def render_users_table(rows: list[tuple], title: str) -> None:
	"""Render one or many user rows as a Rich table."""
	if not rows:
		console.print(
			Panel("No users found.", title=title, border_style="yellow")
		)
		return

	table = Table(title=title, header_style="bold cyan")
	for header in HEADERS:
		table.add_column(header)

	for row in rows:
		table.add_row(*[normalize_cell(value) for value in row])

	console.print(table)
	console.print(
		Panel.fit(f"Total users shown: {len(rows)}", border_style="blue")
	)


def read_one_user() -> None:
	"""Prompt for username and display a single matching user."""
	try:
		username_input = Prompt.ask("Enter username to display")
		username = validate_username(username_input)
	except ValueError as exc:
		console.print(Panel(f"Invalid input: {exc}", border_style="red"))
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
			console.print(
				Panel(f"User '{username}' not found.", border_style="yellow")
			)
			return

		render_users_table([row], f"User: {username}")
	except sqlite3.Error as exc:
		message = str(exc)
		if "no such table" in message.lower():
			console.print(
				Panel(
					"Table 'users' was not found. Run create_database_and_table.py first.",
					border_style="red",
				)
			)
		else:
			console.print(Panel(f"Failed to read user: {exc}", border_style="red"))
	finally:
		if connection is not None:
			connection.close()
			console.print("SQLite connection closed.")


def read_all_users() -> None:
	"""Load and display all users using Rich formatting."""
	try:
		users = fetch_all_users()
		render_users_table(users, "All Users")
	except RuntimeError as exc:
		console.print(Panel(str(exc), border_style="red"))


def create_new_user() -> None:
	"""Create a user via the existing create_user flow."""
	try:
		create_user.main()
	except Exception as exc:
		console.print(Panel(f"Unexpected error: {exc}", border_style="red"))


def update_existing_user() -> None:
	"""Update a user via the existing update_user flow."""
	try:
		update_user.update_user()
	except Exception as exc:
		console.print(Panel(f"Unexpected error: {exc}", border_style="red"))


def delete_existing_user() -> None:
	"""Prompt for username and delete the selected user."""
	try:
		username = Prompt.ask("Enter username to delete")
		delete_user_by_username(username)
	except ValueError as exc:
		console.print(Panel(f"Invalid input: {exc}", border_style="red"))
	except Exception as exc:
		console.print(Panel(f"Unexpected error: {exc}", border_style="red"))


def run_cli_menu() -> None:
	"""Run the interactive command-line menu until exit."""
	actions = {
		"1": create_new_user,
		"2": read_one_user,
		"3": read_all_users,
		"4": update_existing_user,
		"5": delete_existing_user,
	}

	console.print(
		Panel.fit(
			"Welcome to the Registration CLI",
			title="[bold green]Start[/bold green]",
			border_style="green",
		)
	)

	while True:
		print_menu()
		try:
			choice = Prompt.ask(
				"Choose an option",
				default="6",
			).strip()
		except (KeyboardInterrupt, EOFError):
			console.print("\nExiting application.")
			break

		if choice == "6":
			console.print(Panel.fit("Goodbye.", border_style="green"))
			break

		action = actions.get(choice)
		if action is None:
			console.print(
				Panel(
					"Invalid option. Please enter a number from 1 to 6.",
					border_style="red",
				)
			)
			continue

		action()


if __name__ == "__main__":
	run_cli_menu()
