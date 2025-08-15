"""
Feature: Spaced Repetition Scheduler.

This module creates follow-up review tasks for a given topic based on a
spaced repetition schedule (e.g., 1, 3, 7, 14 days later).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.models.core import Task
from notion_calendar_sync.settings import settings

logger = logging.getLogger(__name__)


def schedule_spaced_repetition(
    client: NotionClient,
    source_task_uid: str,
    intervals: list[int] = [1, 3, 7, 14, 30],
    dry_run: bool = False,
):
    """
    Creates a series of review tasks based on a source task with enhanced scheduling.

    Args:
        client: The NotionClient to interact with the API.
        source_task_uid: The UID of the task to base the repetitions on.
        intervals: A list of integers representing the days for future reviews.
        dry_run: If True, logs planned tasks without creating them.
    """
    logger.info(f"Starting spaced repetition scheduling for task UID: {source_task_uid}")
    
    # 1. Find the source task in Notion
    filter_payload = {"property": "UID", "rich_text": {"equals": source_task_uid}}
    try:
        source_tasks = client.query_database_for_sync(
            settings.notion_tasks_db_id, filter_payload
        )
    except Exception as e:
        logger.error(f"Failed to query database for source task: {e}")
        return

    if not source_tasks:
        logger.error(f"Could not find a source task with UID: {source_task_uid}")
        return

    source_task = source_tasks[0]
    if source_task.type != "task":
        logger.error(f"Source item with UID {source_task_uid} is not a task.")
        return

    logger.info(f"Found source task: '{source_task.title}'. Planning {len(intervals)} review sessions.")

    # 2. Calculate dates and create new task objects
    review_tasks: list[Task] = []
    skipped_count = 0
    
    for day in intervals:
        review_date = date.today() + timedelta(days=day)
        review_title = f"📚 Review: {source_task.title}"
        review_uid = f"review-{source_task.uid}-{day}"

        # Check if a review task with this UID already exists
        try:
            existing_check = client.query_database(
                settings.notion_tasks_db_id,
                {"property": "UID", "rich_text": {"equals": review_uid}},
            )
            if existing_check:
                logger.info(f"Review task for day {day} already exists. Skipping.")
                skipped_count += 1
                continue
        except Exception as e:
            logger.warning(f"Could not check for existing review task: {e}")

        # Enhanced notes with study tips
        enhanced_notes = f"""
🔄 **Spaced Repetition Review for:** {source_task.title}

📅 **Original Task Completed:** {source_task.due_date}
⏰ **Review Interval:** {day} days
🎯 **Review Focus:** Active recall and concept reinforcement

**Study Tips:**
• Test yourself without looking at notes first
• Identify any gaps in understanding
• Connect concepts to clinical practice
• Update your notes with new insights

**Original Notes:**
{source_task.notes if source_task.notes else 'No additional notes from original task.'}
        """.strip()

        review_task = Task(
            uid=review_uid,
            title=review_title,
            due_date=review_date,
            priority=source_task.priority,
            status="To Do",
            notes=enhanced_notes,
        )
        review_tasks.append(review_task)

    # 3. Create the tasks in Notion
    if dry_run:
        logger.info(f"DRY RUN: Would create {len(review_tasks)} review tasks, {skipped_count} already exist")
        for task in review_tasks:
            logger.info(
                f"DRY RUN: Would create review task: '{task.title}' due on {task.due_date}"
            )
        return

    created_count = 0
    failed_count = 0
    
    for task in review_tasks:
        try:
            client.create_page(settings.notion_tasks_db_id, task)
            logger.info(f"✅ Created review task: '{task.title}' due on {task.due_date}")
            created_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to create review task '{task.title}': {e}")
            failed_count += 1

    logger.info(f"Spaced repetition scheduling complete: {created_count} created, {skipped_count} skipped, {failed_count} failed")
