"""
A robust client for interacting with the Notion API.

This module handles all the low-level details of making requests to Notion,
including authentication, pagination, rate-limiting, and error handling.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from notion_calendar_sync.models.core import UnifiedSyncItem
from notion_calendar_sync.models.notion_mappers import (
    map_event_to_notion_properties,
    map_notion_page_to_unified_item,
    map_task_to_notion_properties,
)
from notion_calendar_sync.settings import settings
from notion_calendar_sync.utils import NotionPayloadValidator

logger = logging.getLogger(__name__)


class NotionClient:
    """A client for the Notion API."""

    def __init__(
        self, token: str = settings.notion_token, version: str = settings.notion_version
    ):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Notion-Version": version,
                "Content-Type": "application/json",
            }
        )
        self.base_url = "https://api.notion.com/v1"
        self.validator = NotionPayloadValidator()

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Makes a request and handles retries and basic error checking."""
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            logger.error(
                f"HTTP Error: {e.response.status_code} for URL {url}. Response: {e.response.text}"
            )
            # For 4xx client errors, retrying won't help.
            if 400 <= e.response.status_code < 500:
                # Special handling for rate limits, though tenacity should handle Retry-After
                if e.response.status_code == 429:
                    logger.warning("Rate limit exceeded. Retrying...")
                else:
                    # For object_not_found, we want to return None instead of raising
                    if e.response.json().get("code") == "object_not_found":
                        return None
                    raise  # Don't retry other client errors
            raise

    # --- Database Management Methods ---

    def get_database(self, database_id: str) -> dict | None:
        """Retrieves a database object."""
        url = f"{self.base_url}/databases/{database_id}"
        logger.info(f"Retrieving database {database_id}")
        response = self._request("GET", url)
        return response.json() if response else None

    def create_database(self, payload: dict) -> dict:
        """Creates a new database."""
        url = f"{self.base_url}/databases"
        logger.info(f"Creating new database...")
        return self._request("POST", url, json=payload).json()

    def update_database(self, database_id: str, payload: dict) -> dict:
        """Updates an existing database's properties."""
        url = f"{self.base_url}/databases/{database_id}"
        logger.info(f"Updating database {database_id}")
        return self._request("PATCH", url, json=payload).json()

    def list_databases(self) -> list[dict]:
        """
        Lists all databases the client has access to, handling pagination.
        Uses the /search endpoint as recommended by the Notion API.
        """
        results = []
        url = f"{self.base_url}/search"
        payload = {
            "filter": {"value": "database", "property": "object"},
            "page_size": 100,
        }

        while True:
            response = self._request("POST", url, json=payload).json()
            results.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            payload["start_cursor"] = response.get("next_cursor")

        logger.info(f"Found {len(results)} databases accessible by this integration.")
        return results

    # --- Page Management Methods ---

    def query_database(
        self, database_id: str, filter_payload: dict | None = None
    ) -> list[dict]:
        """
        Queries a database and handles pagination to return all results.
        """
        results = []
        url = f"{self.base_url}/databases/{database_id}/query"
        payload: dict[str, Any] = {"page_size": 100}
        if filter_payload:
            payload["filter"] = filter_payload

        while True:
            response = self._request("POST", url, json=payload).json()
            results.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            payload["start_cursor"] = response.get("next_cursor")

        logger.info(f"Queried database {database_id} and found {len(results)} pages.")
        return results

    def query_database_for_sync(self, database_id: str) -> list[UnifiedSyncItem]:
        """Queries a database and maps the results to unified sync items."""
        pages = self.query_database(database_id)
        items = []
        for page in pages:
            item = map_notion_page_to_unified_item(page)
            if item:
                items.append(item)
        return items

    def create_page(self, parent_db_id: str, item: UnifiedSyncItem) -> dict | None:
        """Creates a new page in a database from a sync item."""
        url = f"{self.base_url}/pages"
        if item.type == "event":
            properties = map_event_to_notion_properties(item)
            icon = {"emoji": "📅"}
        elif item.type == "task":
            properties = map_task_to_notion_properties(item)
            icon = {"emoji": "✅"}
        else:
            raise ValueError(f"Unsupported item type: {item.type}")

        payload = {
            "parent": {"database_id": parent_db_id},
            "properties": properties,
            "icon": icon,
        }

        if not self.validator.validate_payload(payload, item.type):
            logger.error(f"Invalid payload for page '{item.title}'. Aborting creation.")
            return None

        logger.info(f"Creating page '{item.title}' in database {parent_db_id}")
        return self._request("POST", url, json=payload).json()

    def update_page(self, page_id: str, item: UnifiedSyncItem) -> dict | None:
        """Updates an existing page's properties from a sync item."""
        url = f"{self.base_url}/pages/{page_id}"
        if item.type == "event":
            properties = map_event_to_notion_properties(item)
        elif item.type == "task":
            properties = map_task_to_notion_properties(item)
        else:
            raise ValueError(f"Unsupported item type: {item.type}")

        payload = {"properties": properties}

        # For validation, we need to construct a mock full payload
        mock_payload_for_validation = {
            "parent": {"database_id": "dummy"},
            "properties": properties,
        }
        if not self.validator.validate_payload(mock_payload_for_validation, item.type):
            logger.error(f"Invalid payload for page '{item.title}'. Aborting update.")
            return None

        logger.info(f"Updating page '{item.title}' ({page_id})")
        return self._request("PATCH", url, json=payload).json()
