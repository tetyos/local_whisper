"""Main window UI for Luca Whisper."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal emitted when window is closed (to minimize to tray)
    close_to_tray = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luca-whisper")
        self.setFixedSize(400, 250)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # App title
        self.title_label = QLabel("luca-whisper")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 15, 20, 15)
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Segoe UI", 14)
        self.status_label.setFont(status_font)
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
        # Hotkey hint
        self.hotkey_label = QLabel("Press Ctrl + Space to start recording")
        self.hotkey_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hotkey_font = QFont("Segoe UI", 11)
        self.hotkey_label.setFont(hotkey_font)
        self.hotkey_label.setObjectName("hotkeyLabel")
        layout.addWidget(self.hotkey_label)
        
        # Add stretch to push everything up
        layout.addStretch()
    
    def _apply_styles(self) -> None:
        """Apply CSS styles to the window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #1a1a2e;
                color: #eaeaea;
            }
            #titleLabel {
                color: #00d4aa;
                padding: 10px;
            }
            #statusFrame {
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #0f3460;
            }
            #statusLabel {
                color: #ffffff;
                background-color: transparent;
            }
            #hotkeyLabel {
                color: #888899;
                background-color: transparent;
            }
        """)
    
    def set_status(self, status: str, is_recording: bool = False) -> None:
        """
        Update the status display.
        
        Args:
            status: Status text to display
            is_recording: Whether currently recording (changes styling)
        """
        self.status_label.setText(status)
        
        if is_recording:
            self.status_label.setStyleSheet("""
                color: #ff4757;
                background-color: transparent;
                font-weight: bold;
            """)
        else:
            self.status_label.setStyleSheet("""
                color: #ffffff;
                background-color: transparent;
                font-weight: normal;
            """)
    
    def set_loading(self, message: str) -> None:
        """Show loading state."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            color: #ffa502;
            background-color: transparent;
        """)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - minimize to tray instead."""
        event.ignore()
        self.hide()
        self.close_to_tray.emit()

