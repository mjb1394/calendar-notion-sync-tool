"""
A calendar provider for reading events from an ICS file or URL.
"""

from __future__ import annotations

import logging

import requests
from ics import Calendar

from notion_calendar_sync.clients.calendar_client import CalendarProvider
from notion_calendar_sync.models.core import Event, generate_uid
from notion_calendar_sync.settings import settings

logger = logging.getLogger(__name__)


class ICSProvider(CalendarProvider):
    """
    Provides events by parsing an ICS file from a URL or local path.
    """

    def __init__(self, ics_url: str = settings.ics_url):
        if not ics_url:
            raise ValueError("ICS_URL must be set to use the ICSProvider.")
        self.ics_url = ics_url

    def get_events(self) -> list[Event]:
        """
        Fetches and parses the ICS file and returns a list of Event models.
        """
        try:
            if self.ics_url.startswith(("http://", "https://")):
                response = requests.get(self.ics_url)
                response.raise_for_status()
                calendar_data = response.text
            else:
                with open(self.ics_url, "r", encoding="utf-8") as f:
                    calendar_data = f.read()

            calendar = Calendar(calendar_data)
        except (requests.RequestException, FileNotFoundError, IOError) as e:
            logger.error(f"Failed to fetch or read ICS from {self.ics_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to parse ICS data: {e}")
            return []

        events = []
        for ics_event in calendar.events:
            # ICS events can be all-day or have specific times
            start_time = ics_event.begin.time() if not ics_event.all_day else None
            end_time = (
                ics_event.end.time()
                if not ics_event.all_day and ics_event.end
                else None
            )

            # Create a stable UID for the event
            uid = generate_uid(
                [
                    "event",
                    ics_event.name or "",
                    "ics",  # Provider name
                    ics_event.location or "",
                    str(ics_event.begin.date()),
                    str(start_time) if start_time else "",
                    str(end_time) if end_time else "",
                ]
            )

            event = Event(
                uid=uid,
                title=ics_event.name or "Untitled Event",
                event_date=ics_event.begin.date(),
                start_time=start_time,
                end_time=end_time,
                location=ics_event.location,
            )
            events.append(event)

        logger.info(f"Parsed {len(events)} events from ICS source.")
        return events
