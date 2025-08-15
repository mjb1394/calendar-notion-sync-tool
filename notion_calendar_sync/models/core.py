"""
Core Pydantic models for the application.

This module defines the data structures for tasks, events, and other
objects used throughout the sync process. It ensures data is validated
and consistent.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field


def generate_uid(parts: list[str]) -> str:
    """Generates a stable, unique ID from a list of strings."""
    key = "|".join(str(p) for p in parts)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def parse_time_flexible(time_str: str | None) -> time | None:
    """Parses a time string that could be in 12-hour or 24-hour format."""
    if not time_str:
        return None
    # Handle common formats, converting to uppercase to standardize AM/PM
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(time_str.strip().upper(), fmt).time()
        except ValueError:
            continue
    # Fallback for ISO format time e.g. "13:30:00" which strptime doesn't handle above
    try:
        return time.fromisoformat(time_str)
    except ValueError:
        logging.warning(f"Could not parse time string '{time_str}' with known formats.")
        return None


class SyncableModel(BaseModel):
    """Base model for all syncable items."""

    uid: str = Field(..., description="A stable, unique identifier for the item.")
    last_edited_time: datetime | None = Field(
        None, description="When the item was last edited in Notion."
    )
    page_id: str | None = Field(None, description="The Notion page ID of the item.")


class Event(SyncableModel):
    """Represents a calendar event."""

    type: Literal["event"] = "event"
    title: str = Field(..., description="The name of the event.")
    event_type: str = Field(
        "General", description="The type of event (e.g., 'Class', 'Clinical')."
    )
    location: str | None = None
    room: str | None = None
    start_time: time | None = Field(None, description="The start time of the event.")
    end_time: time | None = Field(None, description="The end time of the event.")
    event_date: date = Field(..., description="The date of the event.")

    @classmethod
    def from_json(cls, data: dict) -> Event:
        """Creates an Event from a raw dictionary (from json)."""
        uid = generate_uid(
            [
                "event",
                data.get("event", ""),
                data.get("eventtype", ""),
                data.get("location", ""),
                data.get("room") or "",
                data.get("date", ""),
                data.get("start", ""),
                data.get("end", ""),
            ]
        )
        start_time = parse_time_flexible(data.get("start"))
        end_time = parse_time_flexible(data.get("end"))

        return cls(
            uid=uid,
            title=data.get("event", "Untitled Event"),
            event_type=data.get("eventtype", "General"),
            location=data.get("location"),
            room=data.get("room"),
            event_date=date.fromisoformat(data["date"]),
            start_time=start_time,
            end_time=end_time,
        )


class Task(SyncableModel):
    """Represents a task or assignment."""

    type: Literal["task"] = "task"
    title: str = Field(..., description="The name of the task.")
    due_date: date = Field(..., description="The due date of the task.")
    priority: Literal["high", "medium", "low"] = "medium"
    status: str = "To Do"
    notes: str | None = None

    @classmethod
    def from_json(cls, data: dict) -> Task:
        """Creates a Task from a raw dictionary (from json)."""
        uid = generate_uid(
            [
                "task",
                data.get("task", ""),
                data.get("due_date", ""),
                (data.get("priority") or "medium").lower(),
                (data.get("notes") or ""),
            ]
        )

        return cls(
            uid=uid,
            title=data.get("task", "Untitled Task"),
            due_date=date.fromisoformat(data["due_date"]),
            priority=data.get("priority", "medium").lower(),
            notes=data.get("notes"),
        )


# A unified model for easier processing in the sync engine
UnifiedSyncItem = Event or Task
