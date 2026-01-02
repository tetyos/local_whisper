"""System tray icon for Local Whisper."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush
from PyQt6.QtCore import pyqtSignal, QSize


def create_tray_icon(recording: bool = False) -> QIcon:
    """
    Create a simple tray icon programmatically.
    
    Args:
        recording: Whether to show recording state (red) or idle state (green)
    
    Returns:
        QIcon for the system tray
    """
    size = 64
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw circle
    if recording:
        color = QColor("#ff4757")  # Red for recording
    else:
        color = QColor("#00d4aa")  # Green/teal for idle
    
    painter.setBrush(QBrush(color))
    painter.setPen(color)
    
    margin = 8
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    
    # Draw microphone icon (simple representation)
    painter.setBrush(QBrush(QColor("#1a1a2e")))
    painter.setPen(QColor("#1a1a2e"))
    
    # Microphone body
    mic_width = 16
    mic_height = 24
    mic_x = (size - mic_width) // 2
    mic_y = size // 2 - mic_height // 2 - 4
    painter.drawRoundedRect(mic_x, mic_y, mic_width, mic_height, 8, 8)
    
    # Microphone stand
    stand_width = 4
    stand_x = (size - stand_width) // 2
    painter.drawRect(stand_x, mic_y + mic_height, stand_width, 8)
    
    # Base
    base_width = 20
    base_x = (size - base_width) // 2
    painter.drawRect(base_x, mic_y + mic_height + 8, base_width, 4)
    
    painter.end()
    
    return QIcon(pixmap)


class SystemTray(QSystemTrayIcon):
    """System tray icon with context menu."""
    
    # Signals
    show_window_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set initial icon
        self.setIcon(create_tray_icon(recording=False))
        self.setToolTip("local-whisper - Press Ctrl+Space to record")
        
        # Create context menu
        self._create_menu()
        
        # Connect activation signal
        self.activated.connect(self._on_activated)
    
    def _create_menu(self) -> None:
        """Create the right-click context menu."""
        menu = QMenu()
        
        # Show action
        show_action = menu.addAction("Show Window")
        show_action.triggered.connect(self.show_window_requested.emit)
        
        menu.addSeparator()
        
        # Exit action
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_requested.emit)
        
        self.setContextMenu(menu)
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (double-click)."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def set_recording(self, recording: bool) -> None:
        """
        Update the tray icon to show recording state.
        
        Args:
            recording: Whether currently recording
        """
        self.setIcon(create_tray_icon(recording=recording))
        
        if recording:
            self.setToolTip("local-whisper - Recording... Press Ctrl+Space to stop")
        else:
            self.setToolTip("local-whisper - Press Ctrl+Space to record")
    
    def show_message(self, title: str, message: str, 
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
                     duration: int = 3000) -> None:
        """
        Show a notification balloon.
        
        Args:
            title: Notification title
            message: Notification message
            icon: Icon type
            duration: Duration in milliseconds
        """
        self.showMessage(title, message, icon, duration)

