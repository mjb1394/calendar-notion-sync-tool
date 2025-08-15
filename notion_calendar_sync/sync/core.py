"""
The main synchronization engine.

This module orchestrates the entire sync process, from fetching data
from various sources, to creating a sync plan, to executing that plan.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from notion_calendar_sync.clients.notion_client import NotionClient
from notion_calendar_sync.models.core import Event, Task, UnifiedSyncItem
from notion_calendar_sync.settings import settings
from notion_calendar_sync.sync.logic import SyncPlan, create_sync_plan

logger = logging.getLogger(__name__)

from pydantic import ValidationError
from notion_calendar_sync.utils import JsonManager


def read_local_json(path: Path) -> list[UnifiedSyncItem]:
    """Reads the local calendar.json file and converts it to sync items."""
    items: list[UnifiedSyncItem] = []
    if not path.exists():
        logger.warning(f"Local data file not found: {path}")
        return items

    json_manager = JsonManager()
    data_list = json_manager.read_json_file(path)

    for data in data_list:
        item_type = data.get("type")
        try:
            if item_type == "event":
                items.append(Event.from_json(data))
            elif item_type == "task":
                items.append(Task.from_json(data))
        except (ValidationError, Exception) as e:
            logger.error(f"Could not parse item from json: {data}. Error: {e}")
    return items


class SyncEngine:
    """Orchestrates the synchronization between local data and Notion."""

    def __init__(self, notion_client: NotionClient, dry_run: bool = False):
        self.notion_client = notion_client
        self.dry_run = dry_run

    def execute_plan(self, plan: SyncPlan):
        """Executes the actions outlined in a SyncPlan."""
        logger.info("Executing sync plan with %d items to create and %d items to update.", len(plan.create_in_notion), len(plan.update_in_notion))
        if self.dry_run:
            logger.info(
                "DRY RUN: Would create %d pages in Notion.", len(plan.create_in_notion)
            )
            logger.info(
                "DRY RUN: Would update %d pages in Notion.", len(plan.update_in_notion)
            )
            return

        for item in plan.create_in_notion:
            try:
                db_id = (
                    settings.notion_calendar_db_id
                    if item.type == "event"
                    else settings.notion_tasks_db_id
                )
                self.notion_client.create_page(db_id, item)
                logger.info("Successfully created page for item '%s'.", item.title)
            except Exception as e:
                logger.error(f"Failed to create page for item '{item.title}': {e}")

        for item in plan.update_in_notion:
            if not item.page_id:
                logger.warning(f"Cannot update item '{item.title}' without a page_id.")
                continue
            try:
                self.notion_client.update_page(item.page_id, item)
                logger.info("Successfully updated page for item '%s'.", item.title)
            except Exception as e:
                logger.error(f"Failed to update page for item '{item.title}': {e}")

        logger.info("Sync plan executed successfully.")

    def run(self, local_data_path: Path | str = "calendar.json"):
        """
        Executes the full, one-way synchronization from the local file to Notion.
        """
        logger.info("Starting sync: local -> Notion")

        # 1. Fetch items from local source
        local_items = read_local_json(Path(local_data_path))

        # 2. Fetch items from Notion
        notion_events = self.notion_client.query_database_for_sync(
            settings.notion_calendar_db_id
        )
        notion_tasks = self.notion_client.query_database_for_sync(
            settings.notion_tasks_db_id
        )
        notion_items = notion_events + notion_tasks

        # 3. Create a sync plan
        plan = create_sync_plan(notion_items, local_items, strategy="local_to_notion")

        # 4. Execute the plan
        self.execute_plan(plan)

        logger.info("Sync finished.")
