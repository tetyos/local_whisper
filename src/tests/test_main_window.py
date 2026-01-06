"""Tests for the main_window UI module."""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from local_whisper.ui.main_window import MainWindow, ModelCard


@pytest.fixture
def mock_transcriber(monkeypatch):
    """Mock the Transcriber class for UI testing."""
    mock_models = [
        {"name": "tiny", "display_name": "OpenAI Whisper Tiny", "size": "~75 MB", "description": "Fastest"},
        {"name": "base", "display_name": "OpenAI Whisper Base", "size": "~150 MB", "description": "Good balance"},
        {"name": "small", "display_name": "OpenAI Whisper Small", "size": "~500 MB", "description": "Better accuracy"},
    ]
    
    monkeypatch.setattr("local_whisper.ui.main_window.Transcriber.get_available_models", lambda: mock_models)
    monkeypatch.setattr("local_whisper.ui.main_window.Transcriber.is_model_downloaded", lambda x: x == "tiny")
    
    return mock_models


@pytest.fixture
def main_window(qtbot, mock_transcriber):
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestMainWindowInit:
    """Tests for MainWindow initialization."""
    
    def test_window_title(self, main_window):
        """Test window title is set correctly."""
        assert main_window.windowTitle() == "local-whisper"
    
    def test_window_size(self, main_window):
        """Test window has minimum size."""
        assert main_window.minimumWidth() >= 450
        assert main_window.minimumHeight() >= 450
    
    def test_initial_view_is_main(self, main_window):
        """Test that initial view is main view (index 0)."""
        assert main_window.stacked_widget.currentIndex() == 0
    
    def test_has_title_label(self, main_window):
        """Test that title label exists."""
        assert main_window.title_label is not None
        assert "local-whisper" in main_window.title_label.text()
    
    def test_has_status_label(self, main_window):
        """Test that status label exists."""
        assert main_window.status_label is not None
    
    def test_has_hotkey_label(self, main_window):
        """Test that hotkey label exists."""
        assert main_window.hotkey_label is not None
        assert "Ctrl" in main_window.hotkey_label.text()
        assert "Space" in main_window.hotkey_label.text()
    
    def test_has_models_button(self, main_window):
        """Test that models button exists."""
        assert main_window.models_button is not None


class TestMainWindowStatus:
    """Tests for status updates."""
    
    def test_set_status_updates_label(self, main_window):
        """Test that set_status updates the label text."""
        main_window.set_status("Testing status")
        
        assert main_window.status_label.text() == "Testing status"
    
    def test_set_status_recording_style(self, main_window):
        """Test that recording status has special styling."""
        main_window.set_status("Recording...", is_recording=True)
        
        # Check that style contains recording color (red)
        style = main_window.status_label.styleSheet()
        assert "#ff4757" in style or "bold" in style
    
    def test_set_status_normal_style(self, main_window):
        """Test that normal status has default styling."""
        main_window.set_status("Ready", is_recording=False)
        
        style = main_window.status_label.styleSheet()
        assert "normal" in style or "#ffffff" in style
    
    def test_set_status_hides_progress_bar(self, main_window):
        """Test that non-transcribing status hides progress bar."""
        main_window.transcription_progress_bar.setVisible(True)
        
        main_window.set_status("Ready", is_transcribing=False)
        
        assert main_window.transcription_progress_bar.isVisible() is False


class TestMainWindowModel:
    """Tests for model display."""
    
    def test_set_current_model_updates_label(self, main_window):
        """Test that set_current_model updates the display label."""
        main_window.set_current_model("base", "OpenAI Whisper Base")
        
        assert main_window.model_display_label.text() == "OpenAI Whisper Base"
    
    def test_set_current_model_stores_name(self, main_window):
        """Test that set_current_model stores the model name."""
        main_window.set_current_model("small", "OpenAI Whisper Small")
        
        assert main_window.get_current_model() == "small"
    
    def test_set_current_model_empty_shows_no_model(self, main_window):
        """Test that empty model shows 'No model selected'."""
        main_window.set_current_model("", "")
        
        assert "No model" in main_window.model_display_label.text()


class TestMainWindowTranscriptionProgress:
    """Tests for transcription progress display."""
    
    def test_update_transcription_progress_shows_bar(self, main_window):
        """Test that progress update shows the progress bar."""
        main_window.update_transcription_progress(50.0, 5.0, 5.0)
        
        assert main_window.transcription_progress_bar.isVisible()
        assert main_window.eta_label.isVisible()
    
    def test_update_transcription_progress_value(self, main_window):
        """Test that progress value is set correctly."""
        main_window.update_transcription_progress(75.0, 7.5, 2.5)
        
        assert main_window.transcription_progress_bar.value() == 75
    
    def test_update_transcription_progress_eta_format(self, main_window):
        """Test that ETA is formatted correctly."""
        main_window.update_transcription_progress(50.0, 30.0, 30.0)
        
        # 30 seconds should be formatted nicely
        eta_text = main_window.eta_label.text()
        assert "30" in eta_text or "remaining" in eta_text.lower()
    
    def test_update_transcription_progress_finishing(self, main_window):
        """Test finishing state when ETA is very low."""
        main_window.update_transcription_progress(99.0, 10.0, 0.5)
        
        eta_text = main_window.eta_label.text()
        assert "Finishing" in eta_text or "less than" in eta_text.lower()


class TestMainWindowModelSelector:
    """Tests for model selector view."""
    
    def test_models_button_switches_view(self, main_window, qtbot):
        """Test that models button switches to selector view."""
        qtbot.mouseClick(main_window.models_button, Qt.MouseButton.LeftButton)
        
        assert main_window.stacked_widget.currentIndex() == 1
    
    def test_back_button_returns_to_main(self, main_window, qtbot):
        """Test that back button returns to main view."""
        main_window.stacked_widget.setCurrentIndex(1)
        
        qtbot.mouseClick(main_window.back_button, Qt.MouseButton.LeftButton)
        
        assert main_window.stacked_widget.currentIndex() == 0
    
    def test_model_cards_created(self, main_window, mock_transcriber):
        """Test that model cards are created for each model."""
        assert len(main_window._model_cards) == len(mock_transcriber)
    
    def test_use_button_disabled_initially(self, main_window):
        """Test that use button is disabled when no selection."""
        main_window._selected_model = ""
        main_window._update_use_button_state()
        
        assert main_window.use_button.isEnabled() is False


class TestMainWindowDownloading:
    """Tests for download state handling."""
    
    def test_set_downloading_disables_buttons(self, main_window):
        """Test that downloading state disables download buttons."""
        main_window.set_downloading("base", True)
        
        assert main_window._is_downloading is True
        assert main_window.back_button.isEnabled() is False
    
    def test_set_downloading_false_enables_buttons(self, main_window):
        """Test that stopping download enables buttons."""
        main_window.set_downloading("base", True)
        main_window.set_downloading("", False)
        
        assert main_window._is_downloading is False
        assert main_window.back_button.isEnabled() is True
    
    def test_update_download_progress(self, main_window):
        """Test download progress update."""
        main_window.update_download_progress("base", 50.0, "Downloading model.bin")
        
        assert main_window.global_progress_bar.isVisible()
        assert main_window.global_progress_bar.value() == 50
    
    def test_download_complete_hides_progress(self, main_window, mock_transcriber):
        """Test that download complete hides progress bar."""
        main_window.global_progress_bar.setVisible(True)
        
        main_window.download_complete("tiny")
        
        assert main_window.global_progress_bar.isVisible() is False


class TestMainWindowSignals:
    """Tests for signal emissions."""
    
    def test_model_selected_signal(self, main_window, qtbot, mock_transcriber):
        """Test that model_selected signal is emitted."""
        # Select a downloaded model
        main_window._selected_model = "tiny"
        main_window._model_cards["tiny"]._is_downloaded = True
        
        with qtbot.waitSignal(main_window.model_selected, timeout=1000) as blocker:
            main_window._on_use_clicked()
        
        assert blocker.args == ["tiny"]
    
    def test_download_requested_signal(self, main_window, qtbot, mock_transcriber):
        """Test that download_requested signal is emitted."""
        with qtbot.waitSignal(main_window.download_requested, timeout=1000) as blocker:
            main_window._on_download_requested("base")
        
        assert blocker.args == ["base"]
    
    def test_close_to_tray_signal(self, main_window, qtbot):
        """Test that close_to_tray signal is emitted on close."""
        with qtbot.waitSignal(main_window.close_to_tray, timeout=1000):
            main_window.close()


class TestMainWindowLoadingState:
    """Tests for loading state."""
    
    def test_set_loading_updates_status(self, main_window):
        """Test that set_loading updates status with loading message."""
        main_window.set_loading("Loading model...")
        
        assert main_window.status_label.text() == "Loading model..."
    
    def test_set_loading_styling(self, main_window):
        """Test that loading state has warning color."""
        main_window.set_loading("Loading...")
        
        style = main_window.status_label.styleSheet()
        assert "#ffa502" in style  # Orange/warning color


class TestMainWindowModelsButtonState:
    """Tests for models button state."""
    
    def test_set_models_button_enabled(self, main_window):
        """Test enabling models button."""
        main_window.set_models_button_enabled(True)
        
        assert main_window.models_button.isEnabled()
    
    def test_set_models_button_disabled(self, main_window):
        """Test disabling models button."""
        main_window.set_models_button_enabled(False)
        
        assert main_window.models_button.isEnabled() is False


class TestModelCard:
    """Tests for ModelCard widget."""
    
    @pytest.fixture
    def model_card(self, qtbot, monkeypatch):
        """Create a ModelCard for testing."""
        monkeypatch.setattr("local_whisper.ui.main_window.Transcriber.is_model_downloaded", lambda x: False)
        
        model_info = {
            "name": "test-model",
            "display_name": "Test Model",
            "size": "~100 MB",
            "description": "Test description"
        }
        card = ModelCard(model_info)
        qtbot.addWidget(card)
        return card
    
    def test_model_card_displays_name(self, model_card):
        """Test that card displays model name."""
        # Card should have display name visible
        assert model_card.model_display_name == "Test Model"
    
    def test_model_card_has_radio_button(self, model_card):
        """Test that card has radio button."""
        assert model_card.radio_button is not None
    
    def test_model_card_has_download_button_when_not_downloaded(self, model_card):
        """Test that card has download button when not downloaded."""
        assert model_card.download_button is not None
    
    def test_model_card_download_signal(self, model_card, qtbot):
        """Test that download signal is emitted on button click."""
        with qtbot.waitSignal(model_card.download_requested, timeout=1000) as blocker:
            model_card.download_button.click()
        
        assert blocker.args == ["test-model"]
    
    def test_model_card_selected_signal(self, model_card, qtbot):
        """Test that selected signal is emitted on radio selection."""
        with qtbot.waitSignal(model_card.selected, timeout=1000) as blocker:
            model_card.radio_button.setChecked(True)
        
        assert blocker.args == ["test-model"]
    
    def test_model_card_set_download_enabled(self, model_card):
        """Test enabling/disabling download button."""
        model_card.set_download_enabled(False)
        assert model_card.download_button.isEnabled() is False
        
        model_card.set_download_enabled(True)
        assert model_card.download_button.isEnabled() is True
    
    def test_model_card_mark_as_downloaded(self, model_card):
        """Test marking card as downloaded."""
        model_card.mark_as_downloaded()
        
        assert model_card._is_downloaded is True
        assert model_card.download_button.isVisible() is False


class TestFormatTime:
    """Tests for _format_time static method."""
    
    def test_format_time_less_than_second(self, main_window):
        """Test formatting sub-second times."""
        result = main_window._format_time(0.5)
        
        assert "less than 1s" in result
    
    def test_format_time_seconds(self, main_window):
        """Test formatting seconds."""
        result = main_window._format_time(30)
        
        assert "30s" in result
    
    def test_format_time_minutes(self, main_window):
        """Test formatting minutes."""
        result = main_window._format_time(90)
        
        assert "1m" in result and "30s" in result

