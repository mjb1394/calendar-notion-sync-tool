from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Union

from notion_calendar_sync.utils import JsonManager


def format_location(location: str, room: Optional[str]) -> str:
    """Combine location and room info consistently."""
    if room:
        return f"{location} {room}".strip()
    return location


address = {
    "HHS": "Health and Human Sciences Building, 4121 Little Savannah Rd, Cullowhee, NC 28723",
    "ADATC - Black Mountain": "201 Tabernacle Rd, Black Mountain, NC 28711",
}


class Calendar:
    """A class to manage events and tasks for a calendar app, storing data in a JSON file."""

    def __init__(self, json_file: str):
        """
        Initialize the Calendar with a JSON file path.

        Args:
            json_file (str): Path to the JSON file for storing items.
        """
        if not json_file:
            raise ValueError("A JSON file path must be provided.")
        self.json_file: str = json_file
        self.json_manager = JsonManager()
        self.items: List[Dict] = self.json_manager.read_json_file(self.json_file)

    def add_event(
        self,
        event: Union[str, List[str]],
        eventtype: Union[str, List[str]],
        location: Union[str, List[str]],
        date: Union[str, List[str]],
        start: Union[str, List[str]],
        end: Union[str, List[str]],
        room: Union[str, List[str], None] = None,
        repeat: Optional[List[str]] = None,
    ) -> None:
        """
        Add one or more events to the calendar and save to the JSON file.
        """
        new_items = []
        params = (
            [event, eventtype, location, date, start, end, room]
            if room is not None
            else [event, eventtype, location, date, start, end]
        )
        is_list = [isinstance(param, list) for param in params]

        if any(is_list) and not all(is_list):
            raise ValueError("All parameters must be either strings or lists")

        if repeat is not None:
            if not isinstance(repeat, list):
                raise ValueError("Repeat parameter must be a list of dates or None")
            for r_date in repeat:
                try:
                    datetime.strptime(r_date, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(
                        f"Invalid repeat date format: {r_date}. Must be YYYY-MM-DD"
                    )

        if all(is_list):
            lengths = [len(param) for param in params]
            if len(set(lengths)) > 1:
                raise ValueError("All input lists must have the same length")

            for i in range(lengths[0]):
                try:
                    datetime.strptime(date[i], "%Y-%m-%d")
                    datetime.strptime(start[i], "%H:%M")
                    datetime.strptime(end[i], "%H:%M")
                except ValueError as e:
                    raise ValueError(f"Invalid date or time format at index {i}: {e}")

                loc = format_location(location[i], room[i] if room is not None else None)
                event_dict = {
                    "type": "event",
                    "event": event[i],
                    "eventtype": eventtype[i],
                    "location": loc,
                    "date": date[i],
                    "start": start[i],
                    "end": end[i],
                    "room": room[i] if room is not None else None,
                }
                new_items.append(event_dict)

                if repeat:
                    for r_date in repeat:
                        repeat_loc = format_location(
                            location[i], room[i] if room is not None else None
                        )
                        new_items.append({
                            "type": "event",
                            "event": event[i],
                            "eventtype": eventtype[i],
                            "location": repeat_loc,
                            "date": r_date,
                            "start": start[i],
                            "end": end[i],
                            "room": room[i] if room is not None else None,
                        })
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                datetime.strptime(start, "%H:%M")
                datetime.strptime(end, "%H:%M")
            except ValueError as e:
                raise ValueError(f"Invalid date or time format: {e}")

            loc = format_location(location, room)
            event_dict = {
                "type": "event",
                "event": event,
                "eventtype": eventtype,
                "location": loc,
                "date": date,
                "start": start,
                "end": end,
                "room": room,
            }
            new_items.append(event_dict)

            if repeat:
                for r_date in repeat:
                    repeat_loc = format_location(location, room)
                    new_items.append({
                        "type": "event",
                        "event": event,
                        "eventtype": eventtype,
                        "location": repeat_loc,
                        "date": r_date,
                        "start": start,
                        "end": end,
                        "room": room,
                    })

        self.items.extend(new_items)
        self.json_manager.append_to_json_array(self.json_file, new_items)

    def add_task(
        self,
        task: Union[str, List[str]],
        due_date: Union[str, List[str]],
        priority: Union[str, List[str]] = "medium",
        notes: Union[Optional[str], List[Optional[str]]] = None,
        status: Union[str, List[str]] = "To Do",
    ) -> None:
        """
        Add one or more tasks to the calendar and save to the JSON file.
        """
        new_items = []

        # Check if we are dealing with a list of tasks or a single one
        is_list_input = isinstance(task, list)

        # If not list, convert all to lists to handle them uniformly
        if not is_list_input:
            task = [task]
            due_date = [due_date]
            priority = [priority]
            notes = [notes]
            status = [status]

        # Basic validation for list lengths
        if len(task) != len(due_date):
            raise ValueError("Task and due_date lists must have the same length.")

        # Pad other lists if they are shorter than the main task list
        # This is a bit more flexible than the original implementation
        def pad_list(param, length, default_val):
            if not isinstance(param, list):
                return [param] * length
            if len(param) < length:
                return param + [default_val] * (length - len(param))
            return param

        num_tasks = len(task)
        priority = pad_list(priority, num_tasks, "medium")
        notes = pad_list(notes, num_tasks, None)
        status = pad_list(status, num_tasks, "To Do")

        valid_priorities = {"high", "medium", "low"}

        for i in range(num_tasks):
            try:
                datetime.strptime(due_date[i], "%Y-%m-%d")
            except (ValueError, TypeError):
                raise ValueError(f"Invalid due date format for task '{task[i]}': {due_date[i]}. Must be YYYY-MM-DD")

            if priority[i].lower() not in valid_priorities:
                raise ValueError(
                    f"Invalid priority for task '{task[i]}': {priority[i]}. Must be one of {valid_priorities}"
                )

            new_items.append({
                "type": "task",
                "task": task[i],
                "due_date": due_date[i],
                "priority": priority[i].lower(),
                "notes": notes[i],
                "status": status[i],
            })

        self.items.extend(new_items)
        self.json_manager.append_to_json_array(self.json_file, new_items)

    def get_items(self) -> List[Dict]:
        """Return the list of all calendar items."""
        return self.items


# Example usage
if __name__ == "__main__":
    calendar = Calendar("sample_calendar.json")

    # Clear the file for a clean run of the example
    with open(calendar.json_file, "w") as f:
        f.write("[]")

    calendar.add_event(
        event=[
            "BSN Opening Assembly",
            "Julian F. Keith ADATC in Black Mountain",
            "NSG 423 Orientation",
        ],
        eventtype=["Orientation", "Orientation", "Orientation"],
        location=[address["HHS"], address["ADATC - Black Mountain"], address["HHS"]],
        room=["HHS 204", "NA", "HHS 211"],
        date=["2025-08-18", "2025-08-18", "2025-08-18"],
        start=["13:00", "08:20", "15:30"],
        end=["15:00", "10:30", "16:30"],
    )
    calendar.add_task(
        task="Finish report",
        due_date="2025-08-14",
        priority="high",
        notes="Complete the quarterly report for Q3",
    )

    print(f"Total items in calendar: {len(calendar.get_items())}")
    print("Items successfully saved to sample_calendar.json")
