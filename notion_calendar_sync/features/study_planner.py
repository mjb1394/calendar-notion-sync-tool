"""
Feature: Automatic Study Planner.

This module helps students by automatically scheduling study sessions
for an upcoming exam or major assignment.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.models.core import Event
from notion_calendar_sync.settings import settings

logger = logging.getLogger(__name__)


def plan_study_sessions(
    client: NotionClient,
    exam_title: str,
    exam_date: date,
    total_hours: int,
    session_duration_hours: int = 2,
    dry_run: bool = False,
):
    """
    Generates and schedules study blocks in the Notion calendar leading up to an exam.

    Args:
        client: The NotionClient to interact with the API.
        exam_title: The name of the exam to plan for.
        exam_date: The date of the exam.
        total_hours: The total number of hours to study.
        session_duration_hours: The duration of each study block in hours.
        dry_run: If True, will log planned sessions without creating them.
    """
    num_sessions = total_hours // session_duration_hours
    if total_hours % session_duration_hours > 0:
        num_sessions += 1

    logger.info(f"Planning {num_sessions} study session(s) for '{exam_title}'.")

    # Fetch existing events to avoid conflicts
    existing_events = client.query_database_for_sync(settings.notion_calendar_db_id)

    # Create a set of busy slots for faster lookup
    # A busy slot is a tuple of (date, hour)
    busy_slots = set()
    for event in existing_events:
        if event.type == "event" and event.start_time:
            current_time = datetime.combine(event.event_date, event.start_time)
            end_time = (
                datetime.combine(event.event_date, event.end_time)
                if event.end_time
                else current_time + timedelta(hours=1)
            )
            while current_time < end_time:
                busy_slots.add((current_time.date(), current_time.hour))
                current_time += timedelta(hours=1)

    # Work backwards from the day before the exam
    current_date = exam_date - timedelta(days=1)
    sessions_created = 0

    while sessions_created < num_sessions and current_date > date.today():
        # Find available slots in a typical study day (e.g., 9am to 10pm)
        for hour in range(9, 22, session_duration_hours):
            if sessions_created >= num_sessions:
                break

            slot_is_free = True
            for i in range(session_duration_hours):
                if (current_date, hour + i) in busy_slots:
                    slot_is_free = False
                    break

            if slot_is_free:
                start_time = datetime.strptime(f"{hour:02d}:00", "%H:%M").time()
                end_time = (
                    datetime.combine(current_date, start_time)
                    + timedelta(hours=session_duration_hours)
                ).time()

                study_event = Event(
                    uid=f"study-{exam_title.lower().replace(' ','-')}-{current_date.isoformat()}-{start_time.isoformat()}",
                    title=f"Study for: {exam_title}",
                    event_type="Study",
                    event_date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                )

                if dry_run:
                    logger.info(
                        f"DRY RUN: Would create study session: {study_event.title} on {study_event.event_date} from {study_event.start_time} to {study_event.end_time}"
                    )
                else:
                    try:
                        client.create_page(settings.notion_calendar_db_id, study_event)
                        logger.info(
                            f"Created study session for '{exam_title}' on {current_date}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to create study session: {e}")

                sessions_created += 1
                # Add the newly created session to busy_slots to avoid overlap with itself
                for i in range(session_duration_hours):
                    busy_slots.add((current_date, hour + i))

        current_date -= timedelta(days=1)

    if sessions_created < num_sessions:
        logger.warning(
            f"Could only schedule {sessions_created} out of {num_sessions} requested sessions."
        )
    else:
        logger.info("Successfully scheduled all study sessions.")
