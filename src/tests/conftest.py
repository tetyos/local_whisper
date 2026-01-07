"""Shared pytest fixtures for local_whisper tests."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator

import pytest
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture
def temp_settings_dir(tmp_path: Path, monkeypatch) -> Path:
    """
    Create a temporary settings directory and patch APPDATA to use it.
    
    This ensures tests don't interfere with real user settings.
    """
    settings_dir = tmp_path / "local-whisper"
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    # Patch APPDATA environment variable
    monkeypatch.setenv("APPDATA", str(tmp_path))
    
    return settings_dir


@pytest.fixture
def temp_model_dir(temp_settings_dir: Path) -> Path:
    """Create a temporary models directory."""
    model_dir = temp_settings_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


# ============================================================================
# Audio Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_sounddevice(monkeypatch):
    """
    Mock the sounddevice library for testing audio recording.
    
    Returns a mock that can be configured for different test scenarios.
    """
    mock_sd = MagicMock()
    
    # Mock InputStream
    mock_stream = MagicMock()
    mock_sd.InputStream.return_value = mock_stream
    
    # Mock query_devices to return fake devices
    mock_sd.query_devices.return_value = [
        {
            'name': 'Test Microphone',
            'max_input_channels': 2,
            'max_output_channels': 0,
            'default_samplerate': 44100.0
        },
        {
            'name': 'Test Speaker',
            'max_input_channels': 0,
            'max_output_channels': 2,
            'default_samplerate': 44100.0
        }
    ]
    
    monkeypatch.setattr("sounddevice.InputStream", mock_sd.InputStream)
    monkeypatch.setattr("sounddevice.query_devices", mock_sd.query_devices)
    
    return mock_sd


@pytest.fixture
def sample_audio_data() -> np.ndarray:
    """Generate sample audio data for testing."""
    # 1 second of audio at 16kHz
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    # Generate a simple sine wave
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    return audio


# ============================================================================
# Keyboard/Hotkey Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_keyboard(monkeypatch):
    """
    Mock the keyboard library for testing hotkey handling.
    """
    mock_kb = MagicMock()
    
    # Track registered hotkeys
    mock_kb._registered_hotkeys = {}
    
    def add_hotkey(hotkey, callback, suppress=False):
        mock_kb._registered_hotkeys[hotkey] = callback
        return hotkey
    
    def remove_hotkey(hotkey):
        if hotkey in mock_kb._registered_hotkeys:
            del mock_kb._registered_hotkeys[hotkey]
        else:
            raise KeyError(f"Hotkey {hotkey} not registered")
    
    mock_kb.add_hotkey = MagicMock(side_effect=add_hotkey)
    mock_kb.remove_hotkey = MagicMock(side_effect=remove_hotkey)
    
    monkeypatch.setattr("keyboard.add_hotkey", mock_kb.add_hotkey)
    monkeypatch.setattr("keyboard.remove_hotkey", mock_kb.remove_hotkey)
    
    return mock_kb


# ============================================================================
# PyAutoGUI Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_pyautogui(monkeypatch):
    """
    Mock the pyautogui library for testing text output.
    """
    mock_pag = MagicMock()
    
    # Track what was typed
    mock_pag.typed_texts = []
    mock_pag.pressed_keys = []
    mock_pag.hotkeys = []
    
    def write(text, interval=0.0):
        mock_pag.typed_texts.append(text)
    
    def press(key):
        mock_pag.pressed_keys.append(key)
    
    def hotkey(*keys):
        mock_pag.hotkeys.append(keys)
    
    mock_pag.write = MagicMock(side_effect=write)
    mock_pag.press = MagicMock(side_effect=press)
    mock_pag.hotkey = MagicMock(side_effect=hotkey)
    mock_pag.FAILSAFE = True
    
    monkeypatch.setattr("pyautogui.write", mock_pag.write)
    monkeypatch.setattr("pyautogui.press", mock_pag.press)
    monkeypatch.setattr("pyautogui.hotkey", mock_pag.hotkey)
    
    return mock_pag


# ============================================================================
# Whisper Model Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_whisper_model(monkeypatch):
    """
    Mock the WhisperModel for testing transcription without loading real model.
    """
    mock_model = MagicMock()
    
    # Mock segment for transcription results
    mock_segment = MagicMock()
    mock_segment.text = " Hello, this is a test transcription."
    mock_segment.start = 0.0
    mock_segment.end = 2.0
    
    # Mock transcribe to return segments
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    
    # Patch WhisperModel class
    mock_whisper_class = MagicMock(return_value=mock_model)
    monkeypatch.setattr("faster_whisper.WhisperModel", mock_whisper_class)
    
    return mock_model


@pytest.fixture
def mock_hf_api(monkeypatch):
    """
    Mock HuggingFace Hub API for testing model downloads.
    """
    mock_api = MagicMock()
    
    # Mock repo_info response
    mock_sibling = MagicMock()
    mock_sibling.rfilename = "model.bin"
    mock_sibling.size = 1000000  # 1 MB
    
    mock_repo_info = MagicMock()
    mock_repo_info.siblings = [mock_sibling]
    
    mock_api_instance = MagicMock()
    mock_api_instance.repo_info.return_value = mock_repo_info
    
    monkeypatch.setattr("huggingface_hub.HfApi", lambda: mock_api_instance)
    monkeypatch.setattr("huggingface_hub.hf_hub_download", MagicMock())
    
    return mock_api_instance


# ============================================================================
# Fake Model Directory Fixtures
# ============================================================================

@pytest.fixture
def fake_downloaded_model(temp_model_dir: Path) -> str:
    """
    Create a fake downloaded model in the temp directory.
    
    Returns the model name that was created.
    """
    model_name = "tiny"
    repo_name = "Systran/faster-whisper-tiny"
    cache_name = f"models--{repo_name.replace('/', '--')}"
    
    model_path = temp_model_dir / cache_name / "snapshots" / "abc123"
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Create fake model.bin file
    (model_path / "model.bin").write_bytes(b"fake model data")
    
    return model_name


# ============================================================================
# PyQt6 Fixtures (requires pytest-qt)
# ============================================================================

@pytest.fixture(scope="session")
def qapp():
    """
    Create a QApplication instance for the test session.
    
    This is needed because some components (like AudioRecorder) inherit from QObject
    and require a Qt event loop to work properly.
    """
    from PyQt6.QtWidgets import QApplication
    
    # Check if a QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    yield app
    
    # Don't quit the app here - pytest-qt will handle it


@pytest.fixture(autouse=True)
def ensure_qapp(qapp):
    """
    Automatically ensure QApplication exists for all tests.
    
    This is autouse=True so tests don't need to explicitly request it.
    """
    return qapp


# ============================================================================
# App Component Fixtures
# ============================================================================

@pytest.fixture
def mock_app_dependencies(mock_sounddevice, mock_keyboard, mock_pyautogui, mock_whisper_model, temp_settings_dir):
    """
    Combine all mocks needed for testing the main App.
    """
    return {
        'sounddevice': mock_sounddevice,
        'keyboard': mock_keyboard,
        'pyautogui': mock_pyautogui,
        'whisper': mock_whisper_model,
        'settings_dir': temp_settings_dir
    }

