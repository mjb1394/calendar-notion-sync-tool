"""
Application configuration management.

This module uses pydantic-settings to load configuration from environment
variables and/alor .env files. It provides a centralized and validated
source of configuration for the rest of the application.
"""

from __future__ import annotations

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Manually load the .env file to ensure it's available for pydantic-settings
load_dotenv()


class Settings(BaseSettings):
    """
    Manages application-wide settings.
    """

    # --- Notion API Configuration ---
    notion_token: str = Field(..., description="Notion API integration token.")
    notion_version: str = Field("2022-06-28", description="Notion API version.")

    # --- Notion Database IDs ---
    notion_tasks_db_id: str = Field(
        ..., description="ID of the Notion database for tasks."
    )
    notion_calendar_db_id: str = Field(
        ..., description="ID of the Notion database for calendar events."
    )

    # --- Calendar Provider Configuration ---
    calendar_provider: str = Field(
        "ics", description="The calendar provider to use (e.g., 'ics', 'google')."
    )
    ics_url: str | None = Field(
        None, description="URL or file path for the ICS calendar."
    )

    # --- General Settings ---
    local_timezone: str = Field(
        "America/New_York", description="The local timezone for date/time operations."
    )
    log_level: str = Field("INFO", description="The logging level for the application.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single, reusable instance of the settings
settings = Settings()
