import json
from pathlib import Path

CONFIG_FILE = Path("configs.json")

def load_configs():
    """
    Loads all configurations from the JSON file.
    """
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_configs(configs):
    """
    Saves all configurations to the JSON file.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=4)

def get_config(name: str):
    """
    Retrieves a specific configuration by name.
    """
    configs = load_configs()
    return configs.get(name)

def save_config(name: str, config_data: dict):
    """
    Saves a specific configuration.
    """
    configs = load_configs()
    configs[name] = config_data
    save_configs(configs)

def get_active_config_name():
    """
    Gets the name of the active configuration.
    For now, we'll hardcode this to 'default'.
    In the future, this could be stored in a separate file or session.
    """
    return "default"

def get_active_config():
    """
    Retrieves the active configuration.
    """
    active_name = get_active_config_name()
    return get_config(active_name)
