# The purpose of this file is to centralize configuration loading and connection management for the SQLite database
# It connects to SQLite using the settings defined in db.yaml 
# This allows the other scripts to simply call create_sqlite_connection() without worrying about the underlying details


"""SQLite connection helper that reads settings from db.yaml."""

# Import required libraries for downstream tasks
from pathlib import Path
import sqlite3

try:
	import yaml
except ImportError as exc:
	raise ImportError("PyYAML is required. Install it with: pip install pyyaml") from exc


CONFIG_PATH = Path(__file__).with_name("db.yaml")
REQUIRED_KEYS = ("host", "user", "password", "port")


def load_db_config(config_path: Path = CONFIG_PATH) -> dict:
	"""Load and validate the database configuration from YAML."""
	if not config_path.exists():
		raise FileNotFoundError(f"Configuration file not found: {config_path}")

	with config_path.open("r", encoding="utf-8") as file:
		config = yaml.safe_load(file) or {}

	if not isinstance(config, dict):
		raise ValueError("db.yaml must contain key/value pairs.")

	missing_keys = [key for key in REQUIRED_KEYS if key not in config]
	if missing_keys:
		missing = ", ".join(missing_keys)
		raise KeyError(f"Missing required keys in db.yaml: {missing}")

	return config


def create_sqlite_connection(config_path: Path = CONFIG_PATH) -> sqlite3.Connection:
	"""Create and return a SQLite connection based on db.yaml settings."""
	config = load_db_config(config_path)

	host = config["host"]
	user = config["user"]
	password = config["password"]
	port = int(config["port"])

	# SQLite is file-based, but these values are loaded for credential compatibility.
	_ = (host, user, password, port)

	database_name = str(config.get("database", "registration.db"))
	connection = sqlite3.connect(database_name)
	print(f"Connection to SQLite database '{database_name}' established successfully.")
	return connection


if __name__ == "__main__":
	create_sqlite_connection()
