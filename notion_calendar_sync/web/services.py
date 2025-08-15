"""
This module contains service functions that are designed to be called from the Flask web application.
These functions wrap the core business logic of the application and provide a clean interface for the web routes.
"""
from datetime import date

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.features.spaced_repetition import schedule_spaced_repetition
from notion_calendar_sync.features.study_planner import plan_study_sessions
from notion_calendar_sync.features.weekly_review import create_weekly_review_page
from notion_calendar_sync.sync.core import SyncEngine


def run_sync(dry_run: bool = False):
    """
    Runs the Notion sync process.
    """
    try:
        client = NotionClient()
        engine = SyncEngine(notion_client=client, dry_run=dry_run)
        results = engine.run()
        return {
            "success": True,
            "message": "Sync process completed successfully.",
            "results": results,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred during sync: {e}",
        }


def run_plan_study(
    exam_title: str,
    exam_date: date,
    total_hours: int,
    session_duration_hours: int,
    dry_run: bool = False,
):
    """
    Schedules study sessions for an exam.
    """
    try:
        client = NotionClient()
        plan_study_sessions(
            client,
            exam_title=exam_title,
            exam_date=exam_date,
            total_hours=total_hours,
            session_duration_hours=session_duration_hours,
            dry_run=dry_run,
        )
        return {
            "success": True,
            "message": f"Study plan for '{exam_title}' scheduled successfully.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while planning study sessions: {e}",
        }


def run_spaced_repetition(
    source_task_uid: str,
    intervals: list[int],
    dry_run: bool = False,
):
    """
    Schedules spaced repetition review tasks.
    """
    try:
        client = NotionClient()
        schedule_spaced_repetition(
            client,
            source_task_uid=source_task_uid,
            intervals=intervals,
            dry_run=dry_run,
        )
        return {
            "success": True,
            "message": f"Spaced repetition tasks for '{source_task_uid}' scheduled successfully.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred during spaced repetition scheduling: {e}",
        }


def run_weekly_review(dry_run: bool = False):
    """
    Generates a weekly review page in Notion.
    """
    try:
        client = NotionClient()
        create_weekly_review_page(client, dry_run=dry_run)
        return {
            "success": True,
            "message": "Weekly review page generated successfully.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred during weekly review generation: {e}",
        }


def create_notion_page(database_id: str, title: str, properties: dict):
    """
    Creates a new page in a Notion database.
    """
    try:
        client = NotionClient()

        page_properties = {
            "Name": { # Assuming the title property is named "Name"
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }
        page_properties.update(properties)

        client.notion.pages.create(
            parent={"database_id": database_id},
            properties=page_properties
        )
        return {
            "success": True,
            "message": f"Page '{title}' created successfully in database '{database_id}'.",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred while creating the page: {e}",
        }


def get_sync_status():
    """
    Returns the current status of the Notion sync.
    (This is a placeholder for now)
    """
    return {"status": "Not yet implemented"}
