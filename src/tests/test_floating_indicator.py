"""Tests for the floating_indicator module."""

import pytest
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from local_whisper.ui.floating_indicator import (
    FloatingIndicator,
    AudioLevelWidget,
    AudioLevelBar
)


class TestAudioLevelBar:
    """Tests for AudioLevelBar widget."""
    
    def test_init(self, qtbot):
        """Test AudioLevelBar initialization."""
        bar = AudioLevelBar()
        qtbot.addWidget(bar)
        
        assert bar._level == 0.0
        assert bar._target_level == 0.0
    
    def test_set_level(self, qtbot):
        """Test setting the level."""
        bar = AudioLevelBar()
        qtbot.addWidget(bar)
        
        bar.set_level(0.5)
        
        assert bar._target_level == 0.5
    
    def test_set_level_clamps_values(self, qtbot):
        """Test that level values are clamped to 0.0-1.0."""
        bar = AudioLevelBar()
        qtbot.addWidget(bar)
        
        bar.set_level(1.5)
        assert bar._target_level == 1.0
        
        bar.set_level(-0.5)
        assert bar._target_level == 0.0


class TestAudioLevelWidget:
    """Tests for AudioLevelWidget widget."""
    
    def test_init_creates_bars(self, qtbot):
        """Test that AudioLevelWidget creates the specified number of bars."""
        widget = AudioLevelWidget(num_bars=5)
        qtbot.addWidget(widget)
        
        assert len(widget._bars) == 5
    
    def test_default_num_bars(self, qtbot):
        """Test default number of bars is 7."""
        widget = AudioLevelWidget()
        qtbot.addWidget(widget)
        
        assert len(widget._bars) == 7
    
    def test_set_audio_level(self, qtbot):
        """Test setting audio level updates all bars."""
        widget = AudioLevelWidget(num_bars=3)
        qtbot.addWidget(widget)
        
        widget.set_audio_level(0.5)
        
        # All bars should have some level set
        for bar in widget._bars:
            assert bar._target_level >= 0.0


class TestFloatingIndicator:
    """Tests for FloatingIndicator window."""
    
    def test_init(self, qtbot):
        """Test FloatingIndicator initialization."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        assert indicator._is_recording is False
        assert indicator._is_transcribing is False
    
    def test_window_flags(self, qtbot):
        """Test that window has correct flags for always-on-top and no focus stealing."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        flags = indicator.windowFlags()
        
        # Should be frameless
        assert flags & Qt.WindowType.FramelessWindowHint
        # Should stay on top
        assert flags & Qt.WindowType.WindowStaysOnTopHint
        # Should be a tool window
        assert flags & Qt.WindowType.Tool
    
    def test_show_recording(self, qtbot):
        """Test showing recording state."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_recording()
        
        assert indicator._is_recording is True
        assert indicator._is_transcribing is False
        assert indicator._recording_widget.isVisible() is True
        assert indicator._transcribing_widget.isVisible() is False
        assert indicator.isVisible() is True
    
    def test_show_transcribing(self, qtbot):
        """Test showing transcribing state."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_transcribing()
        
        assert indicator._is_recording is False
        assert indicator._is_transcribing is True
        assert indicator._recording_widget.isVisible() is False
        assert indicator._transcribing_widget.isVisible() is True
        assert indicator.isVisible() is True
    
    def test_hide_indicator(self, qtbot):
        """Test hiding the indicator."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_recording()
        indicator.hide_indicator()
        
        assert indicator._is_recording is False
        assert indicator._is_transcribing is False
        assert indicator.isVisible() is False
    
    def test_update_audio_level(self, qtbot):
        """Test updating audio level during recording."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_recording()
        indicator.update_audio_level(0.75)
        
        # Should not crash, audio level widget handles the update
        assert indicator._is_recording is True
    
    def test_update_audio_level_ignored_when_not_recording(self, qtbot):
        """Test that audio level updates are ignored when not recording."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        # Don't show recording, try to update level
        indicator.update_audio_level(0.5)
        
        # Should not crash, just ignore the update
        assert indicator._is_recording is False
    
    def test_update_transcription_progress(self, qtbot):
        """Test updating transcription progress."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_transcribing()
        indicator.update_transcription_progress(50.0, 5.0, 5.0)
        
        assert indicator._progress_bar.value() == 50
        assert "5s" in indicator._eta_label.text()
    
    def test_update_transcription_progress_finishing(self, qtbot):
        """Test transcription progress when finishing up."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        indicator.show_transcribing()
        indicator.update_transcription_progress(95.0, 9.5, 0.5)
        
        assert indicator._progress_bar.value() == 95
        assert "Finishing" in indicator._eta_label.text()
    
    def test_update_transcription_progress_ignored_when_not_transcribing(self, qtbot):
        """Test that progress updates are ignored when not transcribing."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        
        # Get initial value (QProgressBar defaults to -1 when not set)
        initial_value = indicator._progress_bar.value()
        
        # Don't show transcribing, try to update progress
        indicator.update_transcription_progress(50.0, 5.0, 5.0)
        
        # Progress bar should still be at initial value (unchanged)
        assert indicator._progress_bar.value() == initial_value
    
    def test_format_time_seconds(self, qtbot):
        """Test time formatting for seconds."""
        assert FloatingIndicator._format_time(30) == "30s"
    
    def test_format_time_subsecond(self, qtbot):
        """Test time formatting for less than a second."""
        assert FloatingIndicator._format_time(0.5) == "<1s"
    
    def test_format_time_minutes(self, qtbot):
        """Test time formatting for minutes."""
        assert FloatingIndicator._format_time(90) == "1m 30s"


class TestFloatingIndicatorDragging:
    """Tests for FloatingIndicator dragging functionality."""
    
    def test_dragging_starts_on_mouse_press(self, qtbot):
        """Test that dragging starts on left mouse button press."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        indicator.show()
        
        # Simulate mouse press
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import QPointF
        
        event = MagicMock()
        event.button.return_value = Qt.MouseButton.LeftButton
        event.position.return_value = QPointF(10, 10)
        
        indicator.mousePressEvent(event)
        
        assert indicator._dragging is True
    
    def test_dragging_stops_on_mouse_release(self, qtbot):
        """Test that dragging stops on left mouse button release."""
        indicator = FloatingIndicator()
        qtbot.addWidget(indicator)
        indicator.show()
        
        indicator._dragging = True
        
        event = MagicMock()
        event.button.return_value = Qt.MouseButton.LeftButton
        
        indicator.mouseReleaseEvent(event)
        
        assert indicator._dragging is False

