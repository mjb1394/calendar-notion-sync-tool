"""
Mappers to convert between Pydantic models and Notion API objects.

This module is responsible for the "translation" layer, ensuring that
local data models can be correctly represented in Notion and that
Notion data can be correctly parsed back into local models.
"""

from __future__ import annotations

from datetime import datetime

from notion_calendar_sync.models.core import Event, Task, UnifiedSyncItem


# ---------- Notion Property Builders (Primitives) ----------


def notion_title(text: str) -> dict:
    return {"title": [{"type": "text", "text": {"content": text[:2000]}}]}


def notion_rich_text(text: str | None) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": (text or "")[:2000]}}]}


def notion_select(name: str | None) -> dict | None:
    if not name:
        return None
    return {"select": {"name": name[:100]}}


def notion_status(name: str) -> dict:
    return {"status": {"name": name[:100]}}


def notion_date(start_iso: str, end_iso: str | None = None) -> dict:
    return {"date": {"start": start_iso, "end": end_iso}}


# ---------- Model to Notion Mappers ----------


def map_event_to_notion_properties(event: Event) -> dict:
    """Converts an Event model to a Notion page properties dictionary."""
    start_iso = event.event_date.isoformat()
    if event.start_time:
        start_iso = datetime.combine(event.event_date, event.start_time).isoformat()

    end_iso = None
    if event.end_time:
        end_iso = datetime.combine(event.event_date, event.end_time).isoformat()

    properties = {
        "Name": notion_title(event.title),
        "When": notion_date(start_iso, end_iso),
        "Event Type": notion_select(event.event_type),
        "Location": notion_rich_text(event.location),
        "Room": notion_rich_text(event.room),
        "UID": notion_rich_text(event.uid),
    }
    return properties


def map_task_to_notion_properties(task: Task) -> dict:
    """Converts a Task model to a Notion page properties dictionary."""
    properties = {
        "Name": notion_title(task.title),
        "Due": notion_date(task.due_date.isoformat()),
        "Priority": notion_select(task.priority.capitalize()),
        "Status": notion_status(task.status),
        "Notes": notion_rich_text(task.notes),
        "UID": notion_rich_text(task.uid),
    }
    return properties


# ---------- Notion to Model Mappers ----------


def _get_prop(props: dict, name: str, type: str, default: any = None) -> any:
    """Helper to safely extract a property from a Notion page object."""
    prop = props.get(name, {})
    if not prop or not prop.get(type):
        return default

    if type == "rich_text":
        return prop[type][0]["plain_text"] if prop[type] else ""
    if type == "title":
        return prop[type][0]["plain_text"] if prop[type] else ""
    if type == "select":
        return prop[type]["name"] if prop[type] else None
    if type == "status":
        return prop[type]["name"] if prop[type] else None
    if type == "date":
        return prop[type]  # Return the whole date object

    return default


def map_notion_page_to_unified_item(page: dict) -> UnifiedSyncItem | None:
    """
    Converts a Notion page object into either an Event or Task model.

    Determines the type based on the database schema (presence of 'Due' vs 'When').
    """
    props = page.get("properties", {})
    page_id = page.get("id")
    last_edited_str = page.get("last_edited_time")
    last_edited = datetime.fromisoformat(last_edited_str) if last_edited_str else None

    uid = _get_prop(props, "UID", "rich_text")
    if not uid:
        return None  # Cannot process item without a UID

    # Heuristic to determine if it's a Task or Event
    if "Due" in props:  # This is a Task
        due_date_obj = _get_prop(props, "Due", "date")
        due_date = (
            datetime.fromisoformat(due_date_obj["start"]).date()
            if due_date_obj
            else None
        )

        if not due_date:
            return None

        return Task(
            page_id=page_id,
            uid=uid,
            last_edited_time=last_edited,
            title=_get_prop(props, "Name", "title", "Untitled Task"),
            due_date=due_date,
            priority=(_get_prop(props, "Priority", "select") or "medium").lower(),
            status=_get_prop(props, "Status", "status") or "To Do",
            notes=_get_prop(props, "Notes", "rich_text"),
        )

    elif "When" in props:  # This is an Event
        date_obj = _get_prop(props, "When", "date")
        if not date_obj or not date_obj.get("start"):
            return None

        start_dt = datetime.fromisoformat(date_obj["start"])
        end_dt = (
            datetime.fromisoformat(date_obj["end"]) if date_obj.get("end") else None
        )

        return Event(
            page_id=page_id,
            uid=uid,
            last_edited_time=last_edited,
            title=_get_prop(props, "Name", "title", "Untitled Event"),
            event_date=start_dt.date(),
            start_time=start_dt.time() if "T" in date_obj["start"] else None,
            end_time=end_dt.time() if end_dt and "T" in date_obj["end"] else None,
            event_type=_get_prop(props, "Event Type", "select") or "General",
            location=_get_prop(props, "Location", "rich_text"),
            room=_get_prop(props, "Room", "rich_text"),
        )

    return None
