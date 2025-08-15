"""
Feature: Weekly Review Generator.

This module creates a new Notion page that summarizes the past week's
accomplishments and the upcoming week's priorities to help with planning
and reflection.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.models.core import Task
from notion_calendar_sync.settings import settings

logger = logging.getLogger(__name__)


def create_weekly_review_page(client: NotionClient, dry_run: bool = False):
    """
    Creates a new page in the Tasks DB summarizing the week.

    Args:
        client: The NotionClient to interact with the API.
        dry_run: If True, logs the planned page without creating it.
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # 1. Fetch tasks from the last week that are "Done"
    all_tasks = client.query_database_for_sync(settings.notion_tasks_db_id)

    completed_tasks = [
        task
        for task in all_tasks
        if task.type == "task"
        and task.status == "Done"
        and start_of_week - timedelta(days=7) <= task.due_date < start_of_week
    ]

    # 2. Fetch upcoming tasks for this week
    upcoming_tasks = [
        task
        for task in all_tasks
        if task.type == "task" and start_of_week <= task.due_date <= end_of_week
    ]

    # 3. Build the content for the weekly review task
    page_title = f"Weekly Review: {start_of_week.isoformat()}"

    notes_content = []
    notes_content.append("## Last Week's Accomplishments 🎉")
    if completed_tasks:
        for task in completed_tasks:
            notes_content.append(f"- [x] {task.title}")
    else:
        notes_content.append("No completed tasks tracked from last week.")

    notes_content.append("\n## This Week's Priorities 🎯")
    if upcoming_tasks:
        for task in upcoming_tasks:
            notes_content.append(
                f"- [ ] {task.title} (Due: {task.due_date.strftime('%A, %b %d')})"
            )
    else:
        notes_content.append("No upcoming tasks for this week.")

    notes_content.append("\n## Reflection ✨")
    notes_content.append("1. What went well this week?")
    notes_content.append("2. What was challenging?")
    notes_content.append("3. What will I focus on next week to improve?")

    review_notes = "\n".join(notes_content)

    # 4. Create the new task in Notion
    review_task = Task(
        uid=f"weekly-review-{start_of_week.isoformat()}",
        title=page_title,
        due_date=start_of_week,
        priority="medium",
        status="To Do",
        notes=review_notes,
    )

    if dry_run:
        logger.info(f"DRY RUN: Would create weekly review task: '{review_task.title}'")
        logger.info(f"DRY RUN: With notes:\n{review_task.notes}")
        return

    try:
        # Check if it already exists
        existing_check = client.query_database(
            settings.notion_tasks_db_id,
            {"property": "UID", "rich_text": {"equals": review_task.uid}},
        )
        if existing_check:
            logger.info(f"Weekly review for {start_of_week} already exists. Skipping.")
            return

        client.create_page(settings.notion_tasks_db_id, review_task)
        logger.info(f"Successfully created weekly review page: '{review_task.title}'")
    except Exception as e:
        logger.error(f"Failed to create weekly review page: {e}")
