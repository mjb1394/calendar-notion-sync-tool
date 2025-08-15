"""
The main command-line interface for the Notion Student Sync application.
"""

from __future__ import annotations

import logging
from datetime import datetime

import typer

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.features.study_planner import plan_study_sessions
from notion_calendar_sync.features.spaced_repetition import schedule_spaced_repetition
from notion_calendar_sync.features.weekly_review import create_weekly_review_page
from notion_calendar_sync.settings import settings
from notion_calendar_sync.sync.core import SyncEngine

# --- Typer App Initialization ---
app = typer.Typer(
    name="notion_calendar_sync",
    help="A productivity tool for BSN nursing students to sync Notion with their calendars and assist with studying.",
    add_completion=False,
)

# --- Logging Configuration ---
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# --- CLI Commands ---

from notion_calendar_sync.local.setup import SetupManager


@app.command()
def setup():
    """
    Guides you through the first-time setup to create necessary Notion databases.
    """
    manager = SetupManager()
    manager.run()


@app.command()
def sync(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Simulate the sync without making any changes to Notion.",
    )
):
    """
    Synchronizes the local calendar.json file to your Notion databases.
    """
    if not settings.notion_calendar_db_id or not settings.notion_tasks_db_id:
        typer.secho(
            "ERROR: Database IDs not configured. Please run the 'setup' command first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    typer.echo("Starting sync process...")
    client = NotionClient()
    engine = SyncEngine(notion_client=client, dry_run=dry_run)
    engine.run()
    typer.echo("Sync process complete.")


@app.command()
def plan_study(
    exam_title: str = typer.Option(..., "--exam", "-e", help="The title of the exam."),
    exam_date_str: str = typer.Option(
        ..., "--date", "-D", help="The date of the exam in YYYY-MM-DD format."
    ),
    total_hours: int = typer.Option(
        10, "--hours", "-H", help="Total hours you want to study."
    ),
    session_duration: int = typer.Option(
        2, "--duration", "-S", help="Duration of each study session in hours."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Simulate without creating events."
    ),
):
    """
    Automatically schedules study sessions for an exam in your Notion calendar.
    """
    try:
        exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
    except ValueError:
        typer.echo("Error: Please use YYYY-MM-DD format for the date.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Planning study sessions for '{exam_title}'...")
    client = NotionClient()
    plan_study_sessions(
        client,
        exam_title=exam_title,
        exam_date=exam_date,
        total_hours=total_hours,
        session_duration_hours=session_duration,
        dry_run=dry_run,
    )
    typer.echo("Study planning complete.")


@app.command()
def spaced_rep(
    task_uid: str = typer.Option(
        ..., "--uid", "-u", help="The UID of the source task to review."
    ),
    intervals: str = typer.Option(
        "1,3,7,14", "--intervals", "-i", help="Comma-separated list of review days."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Simulate without creating tasks."
    ),
):
    """
    Schedules spaced repetition review tasks for a given source task.
    """
    try:
        interval_list = [int(i.strip()) for i in intervals.split(",")]
    except ValueError:
        typer.echo(
            "Error: Intervals must be a comma-separated list of numbers.", err=True
        )
        raise typer.Exit(1)

    typer.echo(f"Scheduling review tasks for source task UID: {task_uid}")
    client = NotionClient()
    schedule_spaced_repetition(
        client,
        source_task_uid=task_uid,
        intervals=interval_list,
        dry_run=dry_run,
    )
    typer.echo("Spaced repetition scheduling complete.")


@app.command()
def weekly_review(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Simulate without creating the review page."
    ),
):
    """
    Generates a weekly review page in your Notion tasks database.
    """
    typer.echo("Generating weekly review page...")
    client = NotionClient()
    create_weekly_review_page(client, dry_run=dry_run)
    typer.echo("Weekly review page generation complete.")


if __name__ == "__main__":
    app()
