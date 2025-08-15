"""
Unit tests for the Pydantic models and mappers.
"""

from __future__ import annotations

from datetime import date, time

import pytest

from notion_calendar_sync.models.core import Event, Task, generate_uid
from notion_calendar_sync.models.notion_mappers import (
    map_event_to_notion_properties,
    map_notion_page_to_unified_item,
    map_task_to_notion_properties,
)

# --- Fixtures for sample data ---


@pytest.fixture
def sample_json_event() -> dict:
    return {
        "type": "event",
        "event": "Med-Surg Lecture",
        "eventtype": "Class",
        "location": "HHS",
        "room": "201",
        "date": "2025-08-18",
        "start": "09:00",
        "end": "10:15",
    }


@pytest.fixture
def sample_json_task() -> dict:
    return {
        "type": "task",
        "task": "Pharm: Antibiotics",
        "due_date": "2025-08-20",
        "priority": "high",
        "notes": "Cover aminoglycosides",
    }


@pytest.fixture
def sample_notion_event_page() -> dict:
    return {
        "id": "event_page_id_123",
        "last_edited_time": "2025-08-18T12:00:00.000Z",
        "properties": {
            "Name": {"title": [{"plain_text": "Med-Surg Lecture"}]},
            "When": {
                "date": {"start": "2025-08-18T09:00:00", "end": "2025-08-18T10:15:00"}
            },
            "Event Type": {"select": {"name": "Class"}},
            "Location": {"rich_text": [{"plain_text": "HHS"}]},
            "Room": {"rich_text": [{"plain_text": "201"}]},
            "UID": {"rich_text": [{"plain_text": "a6d5c4b3..."}]},
        },
    }


# --- Tests ---


def test_generate_uid_is_stable():
    parts1 = ["event", "title", "2025-01-01"]
    parts2 = ["event", "title", "2025-01-01"]
    assert generate_uid(parts1) == generate_uid(parts2)


def test_generate_uid_is_different():
    parts1 = ["event", "title1", "2025-01-01"]
    parts2 = ["event", "title2", "2025-01-01"]
    assert generate_uid(parts1) != generate_uid(parts2)


def test_event_from_json(sample_json_event):
    event = Event.from_json(sample_json_event)
    assert event.title == "Med-Surg Lecture"
    assert event.event_type == "Class"
    assert event.event_date == date(2025, 8, 18)
    assert event.start_time == time(9, 0)
    assert event.end_time == time(10, 15)
    assert event.uid is not None


def test_task_from_json(sample_json_task):
    task = Task.from_json(sample_json_task)
    assert task.title == "Pharm: Antibiotics"
    assert task.due_date == date(2025, 8, 20)
    assert task.priority == "high"
    assert task.notes == "Cover aminoglycosides"
    assert task.uid is not None


def test_map_event_to_notion_properties():
    event = Event(
        uid="test_uid",
        title="Test Event",
        event_date=date(2025, 1, 1),
        start_time=time(14, 0),
    )
    props = map_event_to_notion_properties(event)
    assert props["Name"]["title"][0]["text"]["content"] == "Test Event"
    assert props["When"]["date"]["start"] == "2025-01-01T14:00:00"
    assert props["UID"]["rich_text"][0]["text"]["content"] == "test_uid"


def test_map_task_to_notion_properties():
    task = Task(
        uid="test_uid_task",
        title="Test Task",
        due_date=date(2025, 1, 5),
        priority="low",
    )
    props = map_task_to_notion_properties(task)
    assert props["Name"]["title"][0]["text"]["content"] == "Test Task"
    assert props["Due"]["date"]["start"] == "2025-01-05"
    assert props["Priority"]["select"]["name"] == "Low"
    assert props["UID"]["rich_text"][0]["text"]["content"] == "test_uid_task"


def test_map_notion_page_to_event(sample_notion_event_page):
    # We need to inject the correct UID to make the test pass
    event_model = Event.from_json(
        {
            "event": "Med-Surg Lecture",
            "eventtype": "Class",
            "location": "HHS",
            "room": "201",
            "date": "2025-08-18",
            "start": "09:00",
            "end": "10:15",
        }
    )
    sample_notion_event_page["properties"]["UID"]["rich_text"][0][
        "plain_text"
    ] = event_model.uid

    item = map_notion_page_to_unified_item(sample_notion_event_page)
    assert isinstance(item, Event)
    assert item.title == "Med-Surg Lecture"
    assert item.event_date == date(2025, 8, 18)
    assert item.start_time == time(9, 0)
    assert item.uid == event_model.uid
