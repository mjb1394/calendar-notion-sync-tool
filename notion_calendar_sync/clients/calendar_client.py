"""
Abstract base class for calendar providers.

This module defines the interface that all calendar providers must adhere to.
This allows the sync engine to work with any calendar integration (ICS,
Google Calendar, etc.) in a consistent way.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from notion_calendar_sync.models.core import Event


class CalendarProvider(ABC):
    """
    An abstract base class for a calendar provider.
    """

    @abstractmethod
    def get_events(self) -> list[Event]:
        """
        Retrieve all events from the calendar source.

        Returns:
            A list of Event objects.
        """
        raise NotImplementedError

    # --- Methods for bi-directional sync (can be implemented later) ---

    def create_event(self, event: Event) -> Event:
        """
        Creates a new event in the calendar.

        Args:
            event: The Event object to create.

        Returns:
            The created Event object, potentially updated with a provider-specific ID.
        """
        raise NotImplementedError

    def update_event(self, event: Event) -> Event:
        """
        Updates an existing event in the calendar.

        Args:
            event: The Event object to update.

        Returns:
            The updated Event object.
        """
        raise NotImplementedError
