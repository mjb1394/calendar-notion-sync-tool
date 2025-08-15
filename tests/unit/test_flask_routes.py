import json
import pytest
from pathlib import Path
from notion_calendar_sync.apps.flask.app import create_app
from notion_calendar_sync.apps.flask.config import Config
from flask import current_app

class TestConfig(Config):
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    # The calendar file path will be set dynamically in the fixture
    CALENDAR_FILE_PATH = ""

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""

    # Create a temporary file to act as the calendar
    calendar_path = Path("test_calendar.json")
    calendar_path.write_text("[]")

    # Update the config with the dynamic path
    TestConfig.CALENDAR_FILE_PATH = str(calendar_path)

    app = create_app(TestConfig)

    yield app

    # clean up / reset resources
    calendar_path.unlink()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def test_index_page(client):
    """
    Test that the index page loads correctly.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Calendar Sync" in response.data

def test_add_item_route(client, app):
    """
    Test that adding an item via the /add route works correctly.
    """
    response = client.post("/add", data={
        "item_type": "event",
        "title": "Test Event",
        "event_type": "Meeting",
        "location": "Online",
        "date": "2025-12-01",
        "start": "10:00",
        "end": "11:00",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Event 'Test Event' added successfully!" in response.data

    # Verify the item was added to the JSON file
    with app.app_context():
        calendar_path = Path(current_app.config["CALENDAR_FILE_PATH"])
        with open(calendar_path, "r") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["event"] == "Test Event"

def test_api_events_route(client, app):
    """
    Test that the /api/events route returns the correct data.
    """
    # First, add an event
    client.post("/add", data={
        "item_type": "event",
        "title": "API Test Event",
        "event_type": "API Test",
        "location": "API",
        "date": "2025-12-02",
        "start": "14:00",
        "end": "15:00",
    })

    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["title"] == "API Test Event"
    assert data[0]["start"] == "2025-12-02T14:00"

def test_notion_tools_page_post(client):
    """
    Test the POST request to the /notion-tools page.
    This test will fail if the services.create_notion_page is not mocked,
    as it would make a real API call. We'll mock it to simulate a successful response.
    """
    # We need to mock the service function to avoid real API calls
    from unittest.mock import patch
    with patch('notion_calendar_sync.web.services.create_notion_page') as mock_create:
        mock_create.return_value = {"success": True, "message": "Page created!"}

        response = client.post("/notion-tools", data={
            "database_id": "test-db-id",
            "page_title": "Test Page from Route",
            "properties_json": "{}"
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Page created!" in response.data
        mock_create.assert_called_once()
