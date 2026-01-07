"""Floating indicator window for recording and transcription status."""

import random
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, 
    QTimer, QPoint, QSize, pyqtProperty
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QScreen

from .styles import COLORS


class AudioLevelBar(QWidget):
    """A single animated bar for audio level visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._level: float = 0.0
        self._target_level: float = 0.0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate)
        self._animation_timer.start(30)  # ~33fps for smooth animation
        
        self.setMinimumWidth(6)
        self.setMinimumHeight(30)
    
    def set_level(self, level: float) -> None:
        """Set the target level (0.0-1.0)."""
        self._target_level = max(0.0, min(1.0, level))
    
    def _animate(self) -> None:
        """Smoothly animate towards target level."""
        # Smooth interpolation
        diff = self._target_level - self._level
        self._level += diff * 0.3  # Easing factor
        
        # Add slight decay when no input
        if self._target_level < 0.05:
            self._level *= 0.85
        
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw the level bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background
        bg_color = QColor(COLORS["border"])
        painter.fillRect(0, 0, width, height, bg_color)
        
        # Level bar (from bottom up)
        bar_height = int(height * self._level)
        if bar_height > 0:
            # Gradient from recording color to accent
            level_color = QColor(COLORS["recording"])
            if self._level > 0.7:
                # Brighter at high levels
                level_color = level_color.lighter(120)
            
            painter.fillRect(0, height - bar_height, width, bar_height, level_color)
        
        # Border
        painter.setPen(QPen(QColor(COLORS["border_hover"]), 1))
        painter.drawRect(0, 0, width - 1, height - 1)


class AudioLevelWidget(QWidget):
    """Widget showing multiple animated bars for audio level visualization."""
    
    def __init__(self, num_bars: int = 7, parent=None):
        super().__init__(parent)
        self._bars: list[AudioLevelBar] = []
        self._current_level: float = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        for i in range(num_bars):
            bar = AudioLevelBar()
            self._bars.append(bar)
            layout.addWidget(bar)
        
        self.setFixedHeight(45)
    
    def set_audio_level(self, level: float) -> None:
        """
        Update the audio level visualization.
        
        Each bar gets a slightly different level for a more dynamic look.
        """
        self._current_level = level
        
        for i, bar in enumerate(self._bars):
            # Add variation to each bar
            variation = random.uniform(0.7, 1.3)
            bar_level = level * variation
            bar.set_level(bar_level)


class FloatingIndicator(QWidget):
    """
    Floating always-on-top indicator window for recording/transcription status.
    
    Shows animated audio level bars during recording and a progress bar
    during transcription.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window flags: frameless, always on top, tool window (doesn't steal focus)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        
        # Semi-transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._dragging = False
        self._drag_offset = QPoint()
        self._is_recording = False
        self._is_transcribing = False
        
        self._setup_ui()
        self._apply_styles()
        self._position_window()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Container widget with background
        self._container = QWidget()
        self._container.setObjectName("floatingContainer")
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(12, 10, 12, 10)
        container_layout.setSpacing(6)
        
        # Recording indicator section
        self._recording_widget = QWidget()
        recording_layout = QVBoxLayout(self._recording_widget)
        recording_layout.setContentsMargins(0, 0, 0, 0)
        recording_layout.setSpacing(4)
        
        # Recording label with mic icon
        self._recording_label = QLabel("🎤 Recording...")
        self._recording_label.setObjectName("floatingRecordingLabel")
        self._recording_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recording_layout.addWidget(self._recording_label)
        
        # Audio level visualization
        self._audio_level_widget = AudioLevelWidget(num_bars=7)
        recording_layout.addWidget(self._audio_level_widget)
        
        container_layout.addWidget(self._recording_widget)
        
        # Transcription progress section
        self._transcribing_widget = QWidget()
        transcribing_layout = QVBoxLayout(self._transcribing_widget)
        transcribing_layout.setContentsMargins(0, 0, 0, 0)
        transcribing_layout.setSpacing(4)
        
        # Transcribing label
        self._transcribing_label = QLabel("Transcribing...")
        self._transcribing_label.setObjectName("floatingTranscribingLabel")
        self._transcribing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        transcribing_layout.addWidget(self._transcribing_label)
        
        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("floatingProgressBar")
        self._progress_bar.setFixedHeight(16)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        transcribing_layout.addWidget(self._progress_bar)
        
        # ETA label
        self._eta_label = QLabel("")
        self._eta_label.setObjectName("floatingEtaLabel")
        self._eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        transcribing_layout.addWidget(self._eta_label)
        
        container_layout.addWidget(self._transcribing_widget)
        
        main_layout.addWidget(self._container)
        
        # Initially hide both sections
        self._recording_widget.setVisible(False)
        self._transcribing_widget.setVisible(False)
        
        # Set fixed width
        self.setFixedWidth(170)
    
    def _apply_styles(self) -> None:
        """Apply styles to the floating indicator."""
        self.setStyleSheet(f"""
            #floatingContainer {{
                background-color: rgba(26, 26, 46, 240);
                border: 2px solid {COLORS["border_hover"]};
                border-radius: 10px;
            }}
            #floatingRecordingLabel {{
                color: {COLORS["recording"]};
                font-size: 12px;
                font-weight: bold;
                background-color: transparent;
            }}
            #floatingTranscribingLabel {{
                color: {COLORS["accent"]};
                font-size: 11px;
                font-weight: bold;
                background-color: transparent;
            }}
            #floatingProgressBar {{
                background-color: {COLORS["border"]};
                border: 1px solid {COLORS["border_hover"]};
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-size: 10px;
            }}
            #floatingProgressBar::chunk {{
                background-color: {COLORS["accent"]};
                border-radius: 3px;
            }}
            #floatingEtaLabel {{
                color: {COLORS["text_muted"]};
                font-size: 10px;
                background-color: transparent;
            }}
        """)
    
    def _position_window(self) -> None:
        """Position the window in the bottom-right corner of the primary screen."""
        from PyQt6.QtWidgets import QApplication
        
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            margin = 20
            x = geometry.right() - self.width() - margin
            y = geometry.bottom() - self.height() - margin
            self.move(x, y)
    
    def show_recording(self) -> None:
        """Show the recording indicator."""
        self._is_recording = True
        self._is_transcribing = False
        self._recording_widget.setVisible(True)
        self._transcribing_widget.setVisible(False)
        self.adjustSize()
        self._position_window()
        self.show()
    
    def show_transcribing(self) -> None:
        """Show the transcription progress indicator."""
        self._is_recording = False
        self._is_transcribing = True
        self._recording_widget.setVisible(False)
        self._transcribing_widget.setVisible(True)
        self._progress_bar.setValue(0)
        self._eta_label.setText("")
        self.adjustSize()
        self._position_window()
        self.show()
    
    def hide_indicator(self) -> None:
        """Hide the floating indicator."""
        self._is_recording = False
        self._is_transcribing = False
        self.hide()
    
    def update_audio_level(self, level: float) -> None:
        """Update the audio level visualization."""
        if self._is_recording:
            self._audio_level_widget.set_audio_level(level)
    
    def update_transcription_progress(self, progress: float, elapsed: float, eta: float) -> None:
        """
        Update transcription progress display.
        
        Args:
            progress: Progress percentage (0-100)
            elapsed: Elapsed time in seconds
            eta: Estimated time remaining in seconds
        """
        if not self._is_transcribing:
            return
        
        self._progress_bar.setValue(int(progress))
        
        if eta < 1 and progress < 100:
            self._eta_label.setText("Finishing...")
        else:
            eta_text = self._format_time(eta)
            self._eta_label.setText(f"ETA: {eta_text}")
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds into a human-readable string."""
        if seconds < 1:
            return "<1s"
        elif seconds < 60:
            return f"{int(seconds)}s"
        else:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
    
    # --- Dragging support ---
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.position().toPoint()
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging."""
        if self._dragging:
            new_pos = self.mapToGlobal(event.position().toPoint()) - self._drag_offset
            self.move(new_pos)
    
    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

