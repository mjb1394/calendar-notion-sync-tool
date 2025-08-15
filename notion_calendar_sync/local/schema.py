from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Union

# --- Official Schemas ---

CALENDAR_DB_SCHEMA = {
    "Name": {"type": "title"},
    "When": {"type": "date"},
    "Event Type": {
        "type": "select",
        "options": [
            {"name": "Orientation", "color": "blue"},
            {"name": "Meeting", "color": "green"},
            {"name": "Study Session", "color": "purple"},
            {"name": "General", "color": "gray"},
        ],
    },
    "Location": {"type": "rich_text"},
    "Room": {"type": "rich_text"},
    "UID": {"type": "rich_text"},
}

TASKS_DB_SCHEMA = {
    "Name": {"type": "title"},
    "Due": {"type": "date"},
    "Priority": {
        "type": "select",
        "options": [
            {"name": "High", "color": "red"},
            {"name": "Medium", "color": "yellow"},
            {"name": "Low", "color": "blue"},
        ],
    },
    "Notes": {"type": "rich_text"},
    "UID": {"type": "rich_text"},
    # NOTE: The 'Status' property (type: "status") is intentionally omitted.
    # Per Notion API limitations, 'status' properties cannot be set during
    # database creation. It must be added in a subsequent 'update' call.
}


class SchemaError(ValueError):
    pass


def _normalize_rich_text(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text, "link": None}}]


def _assert_exactly_one_title(properties: Dict[str, Any]) -> None:
    title_count = sum(1 for p in properties.values() if p.get("type") == "title")
    if title_count != 1:
        raise SchemaError(
            f"Exactly one 'title' property is required; found {title_count}."
        )


def _validate_option_names_unique_no_commas(options: Iterable[str]) -> None:
    names = list(options)
    if any("," in n for n in names):
        bad = [n for n in names if "," in n]
        raise SchemaError(f"Commas are not allowed in option names: {bad}")
    lowered = [n.lower() for n in names]
    if len(lowered) != len(set(lowered)):
        raise SchemaError("Option names must be unique (case-insensitive).")


def _normalize_options(
    options: Iterable[Union[str, Dict[str, Any]]]
) -> list[Dict[str, Any]]:
    normalized = []
    names_for_validation = []
    for opt in options:
        if isinstance(opt, str):
            name = opt
            color = None
        else:
            name = opt.get("name")
            if not name or not isinstance(name, str):
                raise SchemaError(f"Option missing valid 'name': {opt}")
            color = opt.get("color")
        names_for_validation.append(name)
        entry = {"name": name}
        if color:
            entry["color"] = color
        normalized.append(entry)
    _validate_option_names_unique_no_commas(names_for_validation)
    return normalized


def _build_property_schema(
    name: str, spec: Dict[str, Any], *, for_create: bool
) -> Dict[str, Any]:
    ptype = spec.get("type")
    if not ptype or not isinstance(ptype, str):
        raise SchemaError(f"Property '{name}' missing string 'type'.")

    ptype = ptype.strip().lower()

    empty_ok = {
        "checkbox", "created_by", "created_time", "date", "email", "files",
        "people", "phone_number", "rich_text", "title", "url",
        "last_edited_by", "last_edited_time",
    }
    if ptype in empty_ok:
        return {ptype: {}}

    if ptype == "number":
        fmt = spec.get("format")
        return {"number": ({"format": fmt} if fmt else {})}

    if ptype in ("select", "multi_select"):
        options = spec.get("options", [])
        if not isinstance(options, (list, tuple)) or not options:
            raise SchemaError(f"'{name}' {ptype} requires non-empty 'options'.")
        return {ptype: {"options": _normalize_options(options)}}

    if ptype == "status":
        if for_create:
            raise SchemaError(
                "'status' cannot be created via Create Database API. "
                "Create the DB first, then add status via Update Database or the UI."
            )
        status_obj = {}
        if "options" in spec:
            status_obj["options"] = _normalize_options(spec["options"])
        if "groups" in spec:
            status_obj["groups"] = spec["groups"]
        return {"status": status_obj}

    if ptype == "relation":
        dbid = spec.get("database_id")
        if not dbid or not isinstance(dbid, str):
            raise SchemaError(f"'{name}' relation requires 'database_id' (UUID string).")
        rel = {"database_id": dbid}
        sync_name = spec.get("synced_property_name")
        sync_id = spec.get("synced_property_id")
        if sync_name or sync_id:
            rel["dual_property"] = {}
            if sync_name:
                rel["dual_property"]["synced_property_name"] = sync_name
            if sync_id:
                rel["dual_property"]["synced_property_id"] = sync_id
        return {"relation": rel}

    if ptype == "formula":
        expr = spec.get("expression")
        if not expr or not isinstance(expr, str):
            raise SchemaError(f"'{name}' formula requires string 'expression'.")
        return {"formula": {"expression": expr}}

    if ptype == "rollup":
        function = spec.get("function")
        if not function:
            raise SchemaError(f"'{name}' rollup requires 'function'.")
        roll = {"function": function}
        if "relation_property_id" in spec:
            roll["relation_property_id"] = spec["relation_property_id"]
        if "relation_property_name" in spec:
            roll["relation_property_name"] = spec["relation_property_name"]
        if "rollup_property_id" in spec:
            roll["rollup_property_id"] = spec["rollup_property_id"]
        if "rollup_property_name" in spec:
            roll["rollup_property_name"] = spec["rollup_property_name"]

        if not any(k in roll for k in ("relation_property_id", "relation_property_name")):
            raise SchemaError(f"'{name}' rollup requires relation property id or name.")
        if not any(k in roll for k in ("rollup_property_id", "rollup_property_name")):
            raise SchemaError(f"'{name}' rollup requires rollup property id or name.")
        return {"rollup": roll}

    raise SchemaError(f"Unsupported property type '{ptype}' for '{name}'.")


def build_create_database_payload(
    *,
    parent_page_id: str,
    title: str,
    properties: Dict[str, Dict[str, Any]],
    description: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    cover_external_url: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(parent_page_id, str) or not parent_page_id:
        raise SchemaError("'parent_page_id' must be a non-empty string.")
    if not isinstance(title, str) or not title:
        raise SchemaError("'title' must be a non-empty string.")
    if not isinstance(properties, dict) or not properties:
        raise SchemaError("'properties' must be a non-empty dict.")

    notion_props: Dict[str, Any] = {}
    for prop_name, spec in properties.items():
        if not isinstance(prop_name, str) or not prop_name.strip():
            raise SchemaError(f"Invalid property name: {prop_name!r}")
        if not isinstance(spec, dict):
            raise SchemaError(f"Spec for '{prop_name}' must be a dict.")
        notion_props[prop_name] = _build_property_schema(
            prop_name, spec, for_create=True
        )

    _assert_exactly_one_title({k: {"type": list(v.keys())[0]} for k, v in notion_props.items()})

    payload: Dict[str, Any] = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": _normalize_rich_text(title),
        "properties": notion_props,
    }

    if description:
        payload["description"] = _normalize_rich_text(description)
    if icon_emoji:
        payload["icon"] = {"type": "emoji", "emoji": icon_emoji}
    if cover_external_url:
        payload["cover"] = {"type": "external", "external": {"url": cover_external_url}}

    return payload
