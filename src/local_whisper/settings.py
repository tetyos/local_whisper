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


def get_transcription_stats_path() -> Path:
    """Get the path to the transcription stats file."""
    return get_settings_directory() / 'transcription_stats.json'


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


# Transcription stats functions for time estimation

def load_transcription_stats() -> dict[str, Any]:
    """
    Load transcription statistics from file.
    
    Returns:
        Dictionary with transcription stats per model.
        Structure: {model_name: {"samples": [{"audio_duration": float, "transcription_time": float}], "avg_ratio": float}}
    """
    stats_path = get_transcription_stats_path()
    
    if not stats_path.exists():
        return {}
    
    try:
        with open(stats_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_transcription_stats(stats: dict[str, Any]) -> None:
    """
    Save transcription statistics to file.
    
    Args:
        stats: Dictionary of transcription stats
    """
    stats_path = get_transcription_stats_path()
    
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)


def record_transcription_time(model_name: str, audio_duration: float, transcription_time: float) -> None:
    """
    Record a transcription time sample for future estimation.
    
    Args:
        model_name: Name of the model used
        audio_duration: Duration of audio in seconds
        transcription_time: Time taken to transcribe in seconds
    """
    stats = load_transcription_stats()
    
    if model_name not in stats:
        stats[model_name] = {"samples": [], "avg_ratio": 1.0}
    
    # Add new sample (keep last 20 samples per model)
    sample = {"audio_duration": audio_duration, "transcription_time": transcription_time}
    stats[model_name]["samples"].append(sample)
    if len(stats[model_name]["samples"]) > 20:
        stats[model_name]["samples"] = stats[model_name]["samples"][-20:]
    
    # Calculate average ratio (transcription_time / audio_duration)
    samples = stats[model_name]["samples"]
    if samples:
        total_audio = sum(s["audio_duration"] for s in samples)
        total_transcription = sum(s["transcription_time"] for s in samples)
        if total_audio > 0:
            stats[model_name]["avg_ratio"] = total_transcription / total_audio
    
    save_transcription_stats(stats)


def get_estimated_transcription_time(model_name: str, audio_duration: float) -> float:
    """
    Get estimated transcription time for given audio duration and model.
    
    Uses historical data if available, otherwise falls back to model-based estimates.
    
    Args:
        model_name: Name of the model to use
        audio_duration: Duration of audio in seconds
        
    Returns:
        Estimated transcription time in seconds
    """
    stats = load_transcription_stats()
    
    # Default ratios based on model complexity (rough estimates for CPU)
    # Ratio = transcription_time / audio_duration
    default_ratios = {
        "tiny": 0.3,      # Very fast
        "base": 0.5,      # Fast
        "small": 1.0,     # About real-time
        "medium": 2.5,    # Slower
        "large-v3": 5.0,  # Slowest
    }
    
    if model_name in stats and stats[model_name].get("samples"):
        # Use historical average ratio
        ratio = stats[model_name]["avg_ratio"]
    else:
        # Use default estimate
        ratio = default_ratios.get(model_name, 1.0)
    
    return audio_duration * ratio

