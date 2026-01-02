"""Settings module for persisting user preferences."""

import json
import os
from pathlib import Path
from typing import Any


def get_settings_directory() -> Path:
    """Get the directory for storing application settings."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    settings_dir = Path(appdata) / 'local-whisper'
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


def get_settings_path() -> Path:
    """Get the path to the settings file."""
    return get_settings_directory() / 'settings.json'


def get_default_settings() -> dict[str, Any]:
    """Get default settings."""
    return {
        "selected_model": "base"
    }


def load_settings() -> dict[str, Any]:
    """
    Load settings from the settings file.
    
    Returns:
        Dictionary of settings. Returns defaults if file doesn't exist.
    """
    settings_path = get_settings_path()
    
    if not settings_path.exists():
        return get_default_settings()
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Merge with defaults to ensure all keys exist
            defaults = get_default_settings()
            defaults.update(settings)
            return defaults
    except (json.JSONDecodeError, IOError):
        return get_default_settings()


def save_settings(settings: dict[str, Any]) -> None:
    """
    Save settings to the settings file.
    
    Args:
        settings: Dictionary of settings to save
    """
    settings_path = get_settings_path()
    
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


def get_selected_model() -> str:
    """Get the currently selected model name."""
    settings = load_settings()
    return settings.get("selected_model", "base")


def set_selected_model(model_name: str) -> None:
    """
    Set the selected model and save to settings.
    
    Args:
        model_name: Name of the model to select
    """
    settings = load_settings()
    settings["selected_model"] = model_name
    save_settings(settings)

