from __future__ import annotations

import logging

import typer

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.local.schema import (
    CALENDAR_DB_SCHEMA,
    TASKS_DB_SCHEMA,
    build_create_database_payload,
)
from notion_calendar_sync.settings import settings
from notion_calendar_sync.utils import update_env_file

logger = logging.getLogger(__name__)


class SetupManager:
    """Handles the first-time setup of the Notion environment."""

    def __init__(self):
        self.client = NotionClient()

    def run(self):
        """
        Guides the user through setting up the required Notion databases.
        """
        typer.echo("--- Notion Calendar Sync Setup ---")
        if not settings.notion_token:
            typer.secho(
                "ERROR: NOTION_TOKEN is not set. Please set it in your .env file.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)

        parent_page_id = self._get_parent_page()

        # --- Setup Calendar Database ---
        self._ensure_database(
            db_name="Calendar",
            db_config_key="NOTION_CALENDAR_DB_ID",
            db_id=settings.notion_calendar_db_id,
            schema=CALENDAR_DB_SCHEMA,
            parent_page_id=parent_page_id,
            icon="📅",
        )

        # --- Setup Tasks Database ---
        tasks_db_id = self._ensure_database(
            db_name="Tasks",
            db_config_key="NOTION_TASKS_DB_ID",
            db_id=settings.notion_tasks_db_id,
            schema=TASKS_DB_SCHEMA,
            parent_page_id=parent_page_id,
            icon="✅",
        )

        # --- Add Status property to Tasks Database if it was just created ---
        if tasks_db_id:
            self._ensure_status_property(tasks_db_id)

        typer.secho(
            "\nSetup complete! Your .env file has been updated.", fg=typer.colors.GREEN
        )
        typer.echo("You can now run the 'sync' command.")

    def _get_parent_page(self) -> str:
        """
        Prompts the user for the parent page ID where databases will be created.
        """
        typer.echo(
            "\nTo create databases, I need a 'parent page' in Notion."
        )
        typer.echo(
            "Please go to a page in Notion, click the '...' menu, and select 'Copy link'."
        )
        typer.echo("The last part of the URL is the Page ID.")
        parent_page_id = typer.prompt("Please enter the Parent Page ID")
        if not parent_page_id or len(parent_page_id) < 32:
            typer.secho("Invalid Page ID provided.", fg=typer.colors.RED)
            raise typer.Exit(1)
        return parent_page_id

    def _ensure_database(
        self,
        db_name: str,
        db_config_key: str,
        db_id: str | None,
        schema: dict,
        parent_page_id: str,
        icon: str,
    ) -> str | None:
        """
        Checks if a database exists. If not, creates it.
        Returns the database ID if it was newly created, otherwise None.
        """
        typer.echo(f"\nChecking for '{db_name}' database...")
        if db_id and self.client.get_database(db_id):
            typer.secho(
                f"'{db_name}' database already exists (ID: {db_id}). Skipping creation.",
                fg=typer.colors.CYAN,
            )
            return None

        typer.echo(f"'{db_name}' database not found or ID not in .env. Creating it...")
        payload = build_create_database_payload(
            parent_page_id=parent_page_id,
            title=f"Sync - {db_name}",
            properties=schema,
            icon_emoji=icon,
        )
        try:
            response = self.client.create_database(payload)
            new_db_id = response["id"]
            update_env_file(db_config_key, new_db_id)
            typer.secho(
                f"Successfully created '{db_name}' database (ID: {new_db_id}).",
                fg=typer.colors.GREEN,
            )
            return new_db_id
        except Exception as e:
            typer.secho(
                f"Failed to create '{db_name}' database: {e}", fg=typer.colors.RED
            )
            raise typer.Exit(1)

    def _ensure_status_property(self, db_id: str):
        """Adds the 'Status' property to the Tasks database after creation."""
        typer.echo("Adding 'Status' property to Tasks database...")

        db_info = self.client.get_database(db_id)
        if "Status" in db_info.get("properties", {}):
            typer.secho("'Status' property already exists. Skipping.", fg=typer.colors.CYAN)
            return

        status_payload = {
            "properties": {
                "Status": {
                    "status": {
                        "options": [
                            {"name": "To Do", "color": "default"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"},
                        ]
                    }
                }
            }
        }
        try:
            self.client.update_database(db_id, status_payload)
            typer.secho("Successfully added 'Status' property.", fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(
                f"Failed to add 'Status' property: {e}", fg=typer.colors.RED
            )
            raise typer.Exit(1)
