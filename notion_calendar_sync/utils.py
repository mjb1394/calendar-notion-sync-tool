import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Union
from filelock import FileLock, Timeout

# Configure logging - this will be replaced by a centralized config later
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JsonManager:
    """Handles all JSON file operations with file locking, detailed logging, and error handling."""

    def _get_lock(self, file_path: Path) -> FileLock:
        """Creates a lock file object for a given file path."""
        lock_path = file_path.with_suffix(f"{file_path.suffix}.lock")
        return FileLock(lock_path, timeout=10)

    def read_json_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Reads a JSON file with a file lock and returns a list of objects.
        """
        file_path = Path(file_path)
        lock = self._get_lock(file_path)

        try:
            with lock:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}. Returning empty list.")
                    return []

                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        content = f.read()
                        if not content.strip():
                            logger.info(f"File is empty: {file_path}. Returning empty list.")
                            return []
                        data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    else:
                        logger.warning(
                            f"JSON file {file_path} does not contain a list. "
                            "Encapsulating the object in a list."
                        )
                        return [data]
                except json.JSONDecodeError:
                    logger.error(
                        f"Could not decode JSON from {file_path}. "
                        "Please check the file for syntax errors."
                    )
                    return []
        except Timeout:
            logger.error(f"Timeout: Could not acquire lock for reading {file_path}.")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading {file_path}: {e}")
            return []

    def append_to_json_array(
        self, file_path: Union[str, Path], new_items: List[Dict[str, Any]]
    ) -> None:
        """
        Safely and atomically appends new items to a JSON array in a file using a file lock.
        """
        file_path = Path(file_path)
        lock = self._get_lock(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

        try:
            with lock:
                # Read existing data
                if file_path.exists() and file_path.stat().st_size > 0:
                    with file_path.open("r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                            if not isinstance(data, list):
                                logger.error(
                                    f"Existing file {file_path} does not contain a JSON array. Aborting."
                                )
                                raise TypeError("File content is not a list.")
                        except json.JSONDecodeError:
                            logger.error(
                                f"Could not decode JSON from {file_path}. Aborting."
                            )
                            raise
                else:
                    data = []

                # Prepare new content
                data.extend(new_items)

                # Write to temporary file
                with temp_file_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)

                # Atomically move the temporary file to the original file path
                os.replace(temp_file_path, file_path)
                logger.info(f"Successfully wrote {len(data)} items to {file_path}.")

        except Timeout:
            logger.error(f"Timeout: Could not acquire lock for writing to {file_path}.")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while writing to {file_path}: {e}"
            )
            # Clean up the temporary file if it exists
            if temp_file_path.exists():
                os.remove(temp_file_path)
            raise


class NotionPayloadValidator:
    """Validates payloads for the Notion API based on expected structures."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors = []

    def _validate_prop(self, props, name, validator, is_required=True):
        """Helper to run a specific validator on a property."""
        if name not in props:
            if is_required:
                self.errors.append(f"Missing required property: '{name}'")
            return
        validator(name, props[name])

    def _validate_title(self, name, prop):
        if not isinstance(prop, dict) or "title" not in prop:
            self.errors.append(f"'{name}' property is not a valid title object.")
            return
        if not isinstance(prop["title"], list) or not prop["title"]:
            self.errors.append(f"'{name}.title' must be a non-empty list.")
            return
        if not all(
            isinstance(i, dict)
            and i.get("type") == "text"
            and "text" in i
            and "content" in i["text"]
            for i in prop["title"]
        ):
            self.errors.append(f"Invalid item in '{name}.title' list.")

    def _validate_rich_text(self, name, prop):
        if not isinstance(prop, dict) or "rich_text" not in prop:
            self.errors.append(f"'{name}' property is not a valid rich_text object.")
            return
        if not isinstance(prop["rich_text"], list):
            self.errors.append(f"'{name}.rich_text' must be a list.")
            return
        if prop["rich_text"] and not all(
            isinstance(i, dict)
            and i.get("type") == "text"
            and "text" in i
            and "content" in i["text"]
            for i in prop["rich_text"]
        ):
            self.errors.append(f"Invalid item in '{name}.rich_text' list.")

    def _validate_date(self, name, prop):
        if not isinstance(prop, dict) or "date" not in prop:
            self.errors.append(f"'{name}' property is not a valid date object.")
            return
        date_obj = prop["date"]
        if not isinstance(date_obj, dict) or "start" not in date_obj:
            self.errors.append(f"'{name}.date' object must have a 'start' key.")

    def _validate_select(self, name, prop):
        if prop is None:  # Optional select properties can be None
            return
        if not isinstance(prop, dict) or "select" not in prop:
            self.errors.append(f"'{name}' property is not a valid select object.")
            return
        if (
            prop["select"] is not None
            and (
                not isinstance(prop["select"], dict) or "name" not in prop["select"]
            )
        ):
            self.errors.append(f"'{name}.select' object must have a 'name' key.")

    def _validate_status(self, name, prop):
        if not isinstance(prop, dict) or "status" not in prop:
            self.errors.append(f"'{name}' property is not a valid status object.")
            return
        if not isinstance(prop["status"], dict) or "name" not in prop["status"]:
            self.errors.append(f"'{name}.status' object must have a 'name' key.")

    def _validate_event_properties(self, props: Dict[str, Any]):
        self._validate_prop(props, "Name", self._validate_title)
        self._validate_prop(props, "When", self._validate_date)
        self._validate_prop(props, "UID", self._validate_rich_text)
        self._validate_prop(props, "Event Type", self._validate_select, is_required=False)
        self._validate_prop(props, "Location", self._validate_rich_text, is_required=False)

    def _validate_task_properties(self, props: Dict[str, Any]):
        self._validate_prop(props, "Name", self._validate_title)
        self._validate_prop(props, "Due", self._validate_date)
        self._validate_prop(props, "UID", self._validate_rich_text)
        self._validate_prop(props, "Status", self._validate_status, is_required=False)
        self._validate_prop(props, "Priority", self._validate_select, is_required=False)

    def validate_payload(self, payload: Dict[str, Any], item_type: str) -> bool:
        """
        Validates a Notion API payload, checking for required fields and correct structure.
        """
        self.errors.clear()

        if not isinstance(payload, dict):
            self.errors.append("Payload must be a dictionary.")
            return False
        if "parent" not in payload or "database_id" not in payload.get("parent", {}):
            self.errors.append("Payload missing 'parent' with 'database_id'.")
        if "properties" not in payload or not isinstance(payload["properties"], dict):
            self.errors.append("Payload missing or has invalid 'properties'.")
            return False  # Cannot proceed without properties

        properties = payload["properties"]
        if item_type == "event":
            self._validate_event_properties(properties)
        elif item_type == "task":
            self._validate_task_properties(properties)
        else:
            self.errors.append(f"Unknown item type for validation: {item_type}")

        if self.errors:
            for error in self.errors:
                self.logger.error(f"Payload validation error: {error}")
            return False
        return True


def update_env_file(key: str, value: str, env_file_path: Union[str, Path] = ".env"):
    """
    Updates or adds a key-value pair to a .env file.

    Args:
        key (str): The variable name to update.
        value (str): The new value to set.
        env_file_path (str or Path): The path to the .env file.
    """
    env_path = Path(env_file_path)
    lines = []
    key_found = False

    if env_path.exists():
        with env_path.open("r") as f:
            lines = f.readlines()

    with env_path.open("w") as f:
        for line in lines:
            # Preserve comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                f.write(line)
                continue

            # Check if the line contains the key
            if line.strip().startswith(f"{key}="):
                f.write(f'{key}="{value}"\n')
                key_found = True
            else:
                f.write(line)

        # If the key was not found, add it to the end of the file
        if not key_found:
            f.write(f'{key}="{value}"\n')
    logger.info(f"Updated '{key}' in {env_path}")
