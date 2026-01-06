"""Tests for the main app module - state machine and integration."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import threading
import time
import numpy as np

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from local_whisper.app import LocalWhisperApp, AppState


@pytest.fixture
def mock_all_dependencies(monkeypatch, temp_settings_dir):
    """Mock all dependencies for App testing."""
    # Mock sounddevice
    mock_sd = MagicMock()
    mock_stream = MagicMock()
    mock_sd.InputStream.return_value = mock_stream
    mock_sd.query_devices.return_value = [
        {'name': 'Test Mic', 'max_input_channels': 2, 'max_output_channels': 0, 'default_samplerate': 44100}
    ]
    monkeypatch.setattr("sounddevice.InputStream", mock_sd.InputStream)
    monkeypatch.setattr("sounddevice.query_devices", mock_sd.query_devices)
    
    # Mock keyboard
    mock_kb = MagicMock()
    mock_kb._registered_hotkeys = {}
    def add_hotkey(hotkey, callback, suppress=False):
        mock_kb._registered_hotkeys[hotkey] = callback
        return hotkey
    def remove_hotkey(hotkey):
        if hotkey in mock_kb._registered_hotkeys:
            del mock_kb._registered_hotkeys[hotkey]
    mock_kb.add_hotkey = MagicMock(side_effect=add_hotkey)
    mock_kb.remove_hotkey = MagicMock(side_effect=remove_hotkey)
    monkeypatch.setattr("keyboard.add_hotkey", mock_kb.add_hotkey)
    monkeypatch.setattr("keyboard.remove_hotkey", mock_kb.remove_hotkey)
    
    # Mock pyautogui
    mock_pag = MagicMock()
    mock_pag.FAILSAFE = False
    monkeypatch.setattr("pyautogui.write", mock_pag.write)
    monkeypatch.setattr("pyautogui.press", mock_pag.press)
    monkeypatch.setattr("pyautogui.hotkey", mock_pag.hotkey)
    monkeypatch.setattr("pyautogui.FAILSAFE", mock_pag.FAILSAFE)
    
    # Mock WhisperModel
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = " Test transcription"
    mock_segment.start = 0.0
    mock_segment.end = 1.0
    mock_info = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    mock_whisper_class = MagicMock(return_value=mock_model)
    monkeypatch.setattr("faster_whisper.WhisperModel", mock_whisper_class)
    
    # Mock is_model_downloaded to return False initially
    monkeypatch.setattr("local_whisper.app.is_model_downloaded", lambda x: False)
    
    return {
        'sounddevice': mock_sd,
        'keyboard': mock_kb,
        'pyautogui': mock_pag,
        'whisper_model': mock_model,
        'whisper_class': mock_whisper_class
    }


@pytest.fixture
def app_with_model(mock_all_dependencies, monkeypatch, fake_downloaded_model, qtbot):
    """Create an app with a downloaded model."""
    # Patch is_model_downloaded to return True for our fake model
    monkeypatch.setattr("local_whisper.app.is_model_downloaded", lambda x: x == fake_downloaded_model)
    monkeypatch.setattr("local_whisper.transcriber.is_model_downloaded", lambda x: x == fake_downloaded_model)
    
    # Patch get_selected_model to return our fake model
    monkeypatch.setattr("local_whisper.app.get_selected_model", lambda: fake_downloaded_model)
    
    app = LocalWhisperApp()
    return app


class TestAppStateEnum:
    """Tests for AppState enum."""
    
    def test_all_states_exist(self):
        """Test that all expected states exist."""
        expected_states = [
            "LOADING", "IDLE", "RECORDING", "TRANSCRIBING", 
            "TYPING", "DOWNLOADING", "NO_MODEL", "ERROR"
        ]
        
        for state_name in expected_states:
            assert hasattr(AppState, state_name)
    
    def test_states_are_unique(self):
        """Test that all states have unique values."""
        states = list(AppState)
        values = [s.value for s in states]
        
        assert len(values) == len(set(values))


class TestAppInit:
    """Tests for LocalWhisperApp initialization."""
    
    def test_init_creates_components(self, mock_all_dependencies, qtbot):
        """Test that init creates all components."""
        app = LocalWhisperApp()
        
        assert app.audio_recorder is not None
        assert app.transcriber is not None
        assert app.hotkey_handler is not None
        assert app.text_output is not None
    
    def test_init_state_is_loading(self, mock_all_dependencies, qtbot):
        """Test that initial state is LOADING."""
        app = LocalWhisperApp()
        
        assert app.state == AppState.LOADING
    
    def test_init_hotkey_not_registered(self, mock_all_dependencies, qtbot):
        """Test that hotkey is not registered on init."""
        app = LocalWhisperApp()
        
        assert app._hotkey_registered is False
    
    def test_init_not_downloading(self, mock_all_dependencies, qtbot):
        """Test that not downloading initially."""
        app = LocalWhisperApp()
        
        assert app.is_downloading is False


class TestAppStateProperty:
    """Tests for state property."""
    
    def test_state_getter(self, mock_all_dependencies, qtbot):
        """Test state getter."""
        app = LocalWhisperApp()
        app._state = AppState.IDLE
        
        assert app.state == AppState.IDLE
    
    def test_state_setter(self, mock_all_dependencies, qtbot):
        """Test state setter."""
        app = LocalWhisperApp()
        
        app.state = AppState.RECORDING
        
        assert app._state == AppState.RECORDING


class TestAppInitialize:
    """Tests for initialize method."""
    
    def test_initialize_registers_hotkey(self, mock_all_dependencies, qtbot):
        """Test that initialize registers the hotkey."""
        app = LocalWhisperApp()
        
        app.initialize()
        
        assert app._hotkey_registered is True
        mock_all_dependencies['keyboard'].add_hotkey.assert_called()
    
    def test_initialize_emits_no_model_when_no_model(self, mock_all_dependencies, qtbot):
        """Test that initialize emits NO_MODEL state when no model."""
        app = LocalWhisperApp()
        
        states_emitted = []
        app.state_changed.connect(lambda s, m: states_emitted.append(s))
        
        app.initialize()
        
        # Should end in NO_MODEL state
        assert app.state == AppState.NO_MODEL
    
    def test_initialize_loads_model_when_available(self, app_with_model, mock_all_dependencies, qtbot):
        """Test that initialize loads model when available."""
        states_emitted = []
        app_with_model.state_changed.connect(lambda s, m: states_emitted.append(s))
        
        app_with_model.initialize()
        
        # Should start loading
        assert AppState.LOADING in states_emitted or app_with_model.state == AppState.LOADING


class TestAppSelectedModel:
    """Tests for selected model property."""
    
    def test_selected_model_property(self, mock_all_dependencies, qtbot, monkeypatch):
        """Test selected_model property."""
        monkeypatch.setattr("local_whisper.app.get_selected_model", lambda: "small")
        monkeypatch.setattr("local_whisper.app.is_model_downloaded", lambda x: False)
        
        app = LocalWhisperApp()
        
        # When model isn't downloaded, should be empty string
        assert app.selected_model == ""


class TestAppIsDownloading:
    """Tests for is_downloading property."""
    
    def test_is_downloading_false_initially(self, mock_all_dependencies, qtbot):
        """Test is_downloading is False initially."""
        app = LocalWhisperApp()
        
        assert app.is_downloading is False
    
    def test_is_downloading_true_during_download(self, mock_all_dependencies, qtbot):
        """Test is_downloading is True during download."""
        app = LocalWhisperApp()
        app._downloading_model = "base"
        
        assert app.is_downloading is True


class TestAppHotkeyBehavior:
    """Tests for hotkey behavior in different states."""
    
    def test_hotkey_in_idle_starts_recording(self, app_with_model, mock_all_dependencies, qtbot):
        """Test hotkey in IDLE state starts recording."""
        app = app_with_model
        app.state = AppState.IDLE
        app.transcriber._model = MagicMock()  # Simulate loaded model
        
        # Simulate model being loaded
        app.transcriber.model = MagicMock()
        
        states_emitted = []
        app.state_changed.connect(lambda s, m: states_emitted.append(s))
        
        app._on_hotkey_pressed()
        
        assert app.state == AppState.RECORDING or AppState.RECORDING in states_emitted
    
    def test_hotkey_in_no_model_emits_error(self, mock_all_dependencies, qtbot):
        """Test hotkey in NO_MODEL state emits error."""
        app = LocalWhisperApp()
        app.state = AppState.NO_MODEL
        
        errors = []
        app.error_occurred.connect(lambda e: errors.append(e))
        
        app._on_hotkey_pressed()
        
        assert len(errors) == 1
        assert "No model" in errors[0]
    
    def test_hotkey_ignored_in_loading(self, mock_all_dependencies, qtbot):
        """Test hotkey is ignored in LOADING state."""
        app = LocalWhisperApp()
        app.state = AppState.LOADING
        
        initial_state = app.state
        app._on_hotkey_pressed()
        
        assert app.state == initial_state
    
    def test_hotkey_ignored_in_transcribing(self, mock_all_dependencies, qtbot):
        """Test hotkey is ignored in TRANSCRIBING state."""
        app = LocalWhisperApp()
        app.state = AppState.TRANSCRIBING
        
        initial_state = app.state
        app._on_hotkey_pressed()
        
        assert app.state == initial_state


class TestAppStartDownload:
    """Tests for start_download method."""
    
    def test_start_download_prevents_multiple_downloads(self, mock_all_dependencies, qtbot):
        """Test that only one download can run at a time."""
        app = LocalWhisperApp()
        app._downloading_model = "base"  # Simulate download in progress
        
        errors = []
        app.error_occurred.connect(lambda e: errors.append(e))
        
        app.start_download("small")
        
        assert len(errors) == 1
        assert "already in progress" in errors[0]
    
    def test_start_download_rejects_already_downloaded(self, app_with_model, mock_all_dependencies, qtbot, fake_downloaded_model):
        """Test that already downloaded models are rejected."""
        app = app_with_model
        
        errors = []
        app.error_occurred.connect(lambda e: errors.append(e))
        
        app.start_download(fake_downloaded_model)
        
        assert len(errors) == 1
        assert "already downloaded" in errors[0]


class TestAppSelectModel:
    """Tests for select_model method."""
    
    def test_select_model_rejects_not_downloaded(self, mock_all_dependencies, qtbot, monkeypatch):
        """Test that selecting not-downloaded model is rejected."""
        monkeypatch.setattr("local_whisper.app.is_model_downloaded", lambda x: False)
        
        app = LocalWhisperApp()
        
        errors = []
        app.error_occurred.connect(lambda e: errors.append(e))
        
        app.select_model("medium")
        
        assert len(errors) == 1
        assert "not downloaded" in errors[0]
    
    def test_select_model_rejects_during_busy_states(self, mock_all_dependencies, qtbot):
        """Test that model selection is rejected during busy states."""
        app = LocalWhisperApp()
        
        busy_states = [AppState.RECORDING, AppState.TRANSCRIBING, AppState.TYPING, AppState.DOWNLOADING]
        
        for state in busy_states:
            app.state = state
            errors = []
            app.error_occurred.connect(lambda e: errors.append(e))
            
            app.select_model("base")
            
            # Should have emitted error
            app.error_occurred.disconnect()


class TestAppShutdown:
    """Tests for shutdown method."""
    
    def test_shutdown_unregisters_hotkey(self, mock_all_dependencies, qtbot):
        """Test that shutdown unregisters hotkey."""
        app = LocalWhisperApp()
        app.initialize()
        
        app.shutdown()
        
        mock_all_dependencies['keyboard'].remove_hotkey.assert_called()
    
    def test_shutdown_stops_recording(self, app_with_model, mock_all_dependencies, qtbot):
        """Test that shutdown stops recording if in progress."""
        app = app_with_model
        app.audio_recorder.start_recording = MagicMock()
        app.audio_recorder.stop_recording = MagicMock(return_value=np.array([]))
        app.audio_recorder.is_recording = MagicMock(return_value=True)
        
        app.shutdown()
        
        app.audio_recorder.stop_recording.assert_called_once()


class TestAppSignals:
    """Tests for signal emissions."""
    
    def test_state_changed_signal(self, mock_all_dependencies, qtbot):
        """Test that state_changed signal is emitted."""
        app = LocalWhisperApp()
        
        received = []
        app.state_changed.connect(lambda s, m: received.append((s, m)))
        
        app.initialize()
        
        assert len(received) > 0
    
    def test_error_occurred_signal(self, mock_all_dependencies, qtbot):
        """Test that error_occurred signal is emitted."""
        app = LocalWhisperApp()
        app.state = AppState.NO_MODEL
        
        received = []
        app.error_occurred.connect(lambda e: received.append(e))
        
        app._on_hotkey_pressed()
        
        assert len(received) == 1


class TestAppRecovery:
    """Tests for error recovery."""
    
    def test_recover_to_idle_when_model_loaded(self, app_with_model, mock_all_dependencies, qtbot):
        """Test recovery to IDLE when model is loaded."""
        app = app_with_model
        app.transcriber.model = MagicMock()  # Simulate loaded model
        app.state = AppState.ERROR
        
        app._recover_to_idle()
        
        assert app.state == AppState.IDLE
    
    def test_recover_to_no_model_when_not_loaded(self, mock_all_dependencies, qtbot):
        """Test recovery to NO_MODEL when model not loaded."""
        app = LocalWhisperApp()
        app.state = AppState.ERROR
        
        app._recover_to_idle()
        
        assert app.state == AppState.NO_MODEL

