import json
import pytest
from pathlib import Path
import threading
import time
from notion_calendar_sync.utils import JsonManager

@pytest.fixture
def json_manager():
    """Returns an instance of JsonManager."""
    return JsonManager()

@pytest.fixture
def temp_json_file(tmp_path):
    """Creates a temporary JSON file for testing."""
    file_path = tmp_path / "test.json"
    file_path.write_text("[]")
    return file_path

def test_read_empty_json_file(json_manager, temp_json_file):
    """Test reading an empty JSON file returns an empty list."""
    data = json_manager.read_json_file(temp_json_file)
    assert data == []

def test_read_non_existent_file(json_manager, tmp_path):
    """Test reading a non-existent file returns an empty list."""
    data = json_manager.read_json_file(tmp_path / "non_existent.json")
    assert data == []

def test_append_to_json_array(json_manager, temp_json_file):
    """Test appending new items to the JSON array."""
    new_items = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
    json_manager.append_to_json_array(temp_json_file, new_items)

    with open(temp_json_file, "r") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["name"] == "test1"

    # Append again to test with existing data
    more_items = [{"id": 3, "name": "test3"}]
    json_manager.append_to_json_array(temp_json_file, more_items)

    with open(temp_json_file, "r") as f:
        data = json.load(f)

    assert len(data) == 3
    assert data[2]["name"] == "test3"

def test_file_locking_prevents_race_conditions(json_manager, temp_json_file):
    """
    Simulate a race condition by having multiple threads append to the same file.
    The file lock should prevent data corruption.
    """
    num_threads = 5
    items_per_thread = 10

    def worker(thread_id):
        items_to_add = [
            {"thread": thread_id, "item": i} for i in range(items_per_thread)
        ]
        # Add a small random delay to increase chances of collision without locking
        time.sleep(0.01 * (thread_id % 2))
        json_manager.append_to_json_array(temp_json_file, items_to_add)

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Verify the final file content
    with open(temp_json_file, "r") as f:
        data = json.load(f)

    expected_total_items = num_threads * items_per_thread
    assert len(data) == expected_total_items

    # Check that data from all threads is present
    thread_counts = {i: 0 for i in range(num_threads)}
    for item in data:
        thread_counts[item['thread']] += 1

    for i in range(num_threads):
        assert thread_counts[i] == items_per_thread
