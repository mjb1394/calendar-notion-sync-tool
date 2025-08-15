"""
Core synchronization logic, including diffing and conflict resolution.

This module contains the "brains" of the sync engine. It compares items
from different sources and creates a plan of action (what to create,
update, or delete).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from notion_calendar_sync.models.core import UnifiedSyncItem

logger = logging.getLogger(__name__)


@dataclass
class SyncPlan:
    """
    Represents the set of actions to be taken during a sync operation.
    """

    create_in_notion: list[UnifiedSyncItem] = field(default_factory=list)
    update_in_notion: list[UnifiedSyncItem] = field(default_factory=list)
    # For bi-directional sync in the future:
    # create_in_calendar: list[UnifiedSyncItem] = field(default_factory=list)
    # update_in_calendar: list[UnifiedSyncItem] = field(default_factory=list)


def _items_are_different(item1: UnifiedSyncItem, item2: UnifiedSyncItem) -> bool:
    """
    Compares two sync items to see if they have meaningful differences.

    This ignores fields that are expected to be different, like page_id or
    last_edited_time.
    """
    # Exclude fields that don't represent a substantive change
    exclude_fields = {"page_id", "last_edited_time"}
    dict1 = item1.model_dump(exclude=exclude_fields)
    dict2 = item2.model_dump(exclude=exclude_fields)
    return dict1 != dict2


def create_sync_plan(
    notion_items: list[UnifiedSyncItem],
    local_items: list[UnifiedSyncItem],
    strategy: str = "local_to_notion",
) -> SyncPlan:
    """
    Compares items from Notion and a local source to generate a sync plan.

    Args:
        notion_items: A list of items fetched from the Notion API.
        local_items: A list of items from the local source (e.g., json).
        strategy: The synchronization strategy to use.
                  - "local_to_notion": One-way sync. Local changes are pushed to Notion.

    Returns:
        A SyncPlan object detailing the necessary operations.
    """
    plan = SyncPlan()
    notion_map = {item.uid: item for item in notion_items}

    if strategy == "local_to_notion":
        for local_item in local_items:
            notion_item = notion_map.get(local_item.uid)

            if not notion_item:
                # Item exists locally but not in Notion -> create it in Notion
                plan.create_in_notion.append(local_item)
                logger.debug(
                    f"Plan: Create '{local_item.title}' in Notion (UID: {local_item.uid})"
                )
            else:
                # Item exists in both places. Check if an update is needed.
                # We copy the page_id from the Notion item to the local one
                # so the update operation knows which page to target.
                local_item.page_id = notion_item.page_id
                if _items_are_different(local_item, notion_item):
                    plan.update_in_notion.append(local_item)
                    logger.debug(
                        f"Plan: Update '{local_item.title}' in Notion (UID: {local_item.uid})"
                    )

    else:
        raise NotImplementedError(f"Sync strategy '{strategy}' is not yet supported.")

    logger.info(
        f"Sync plan created: "
        f"{len(plan.create_in_notion)} to create, "
        f"{len(plan.update_in_notion)} to update."
    )
    return plan
