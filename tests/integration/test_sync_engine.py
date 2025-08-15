"""
Integration tests for the SyncEngine and related logic.

These tests mock the NotionClient to verify that the sync logic
works correctly without making actual network calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from notion_calendar_sync.models.core import Event, Task
from notion_calendar_sync.sync.core import SyncEngine
from notion_calendar_sync.sync.logic import create_sync_plan


@pytest.fixture
def mock_notion_client() -> MagicMock:
    """A mock NotionClient that can be used to track API calls."""
    client = MagicMock()
    client.query_database_for_sync.return_value = []
    client.create_page.return_value = {}
    client.update_page.return_value = {}
    return client


@pytest.fixture
def local_items() -> list[Event | Task]:
    """Sample local items, as if read from calendar.json."""
    event = Event.from_json(
        {
            "type": "event",
            "event": "Test Event",
            "eventtype": "Class",
            "date": "2025-09-01",
            "start": "10:00",
            "end": "11:00",
        }
    )
    task = Task.from_json(
        {
            "type": "task",
            "task": "Test Task",
            "due_date": "2025-09-05",
        }
    )
    return [event, task]


def test_create_sync_plan_for_new_items(local_items):
    """Test that the plan correctly identifies items to be created."""
    plan = create_sync_plan(notion_items=[], local_items=local_items)

    assert len(plan.create_in_notion) == 2
    assert len(plan.update_in_notion) == 0
    assert plan.create_in_notion[0].title == "Test Event"
    assert plan.create_in_notion[1].title == "Test Task"


def test_create_sync_plan_for_existing_items_no_change(local_items):
    """Test that the plan is empty when sources are identical."""
    # The Notion items are identical to the local items
    plan = create_sync_plan(notion_items=local_items, local_items=local_items)

    assert len(plan.create_in_notion) == 0
    assert len(plan.update_in_notion) == 0


def test_create_sync_plan_for_items_to_update(local_items):
    """Test that the plan correctly identifies items to be updated."""
    notion_item = local_items[0].model_copy(deep=True)
    notion_item.title = "Old Title"  # This is the change
    notion_item.page_id = "page_id_to_update"

    plan = create_sync_plan(notion_items=[notion_item], local_items=[local_items[0]])

    assert len(plan.create_in_notion) == 0
    assert len(plan.update_in_notion) == 1
    updated_item = plan.update_in_notion[0]
    assert updated_item.title == "Test Event"
    assert updated_item.page_id == "page_id_to_update"


def test_sync_engine_executes_create_plan(mock_notion_client, local_items, monkeypatch):
    """Verify that the engine calls create_page for new items."""
    # Mock the function that reads local files
    monkeypatch.setattr("notion_calendar_sync.sync.core.read_local_json", lambda path: local_items)

    engine = SyncEngine(notion_client=mock_notion_client)
    engine.run()

    # Assert that create_page was called twice
    assert mock_notion_client.create_page.call_count == 2
    # Assert that update_page was not called
    assert mock_notion_client.update_page.call_count == 0

    # Check the arguments of the first call
    first_call_args = mock_notion_client.create_page.call_args_list[0].args
    assert first_call_args[1].title == "Test Event"


def test_sync_engine_executes_update_plan(mock_notion_client, local_items, monkeypatch):
    """Verify that the engine calls update_page for existing items."""
    notion_item = local_items[0].model_copy(deep=True)
    notion_item.title = "An Old Title"
    notion_item.page_id = "page_id_123"

    # Mock the Notion client to return this one item
    mock_notion_client.query_database_for_sync.return_value = [notion_item]
    # Mock the local file reader
    monkeypatch.setattr(
        "notion_calendar_sync.sync.core.read_local_json", lambda path: [local_items[0]]
    )

    engine = SyncEngine(notion_client=mock_notion_client)
    engine.run()

    assert mock_notion_client.create_page.call_count == 0
    assert mock_notion_client.update_page.call_count == 1

    update_call_args = mock_notion_client.update_page.call_args.args
    assert update_call_args[0] == "page_id_123"  # Check page_id
    assert update_call_args[1].title == "Test Event"  # Check that it's the new version


def test_sync_engine_dry_run(mock_notion_client, local_items, monkeypatch):
    """Verify that dry_run prevents any actual API calls."""
    monkeypatch.setattr("notion_calendar_sync.sync.core.read_local_json", lambda path: local_items)

    engine = SyncEngine(notion_client=mock_notion_client, dry_run=True)
    engine.run()

    assert mock_notion_client.create_page.call_count == 0
    assert mock_notion_client.update_page.call_count == 0
