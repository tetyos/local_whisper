"""Main window UI for Local Whisper."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal emitted when window is closed (to minimize to tray)
    close_to_tray = pyqtSignal()
    # Signal emitted when user clicks the Models button
    open_model_selector = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("local-whisper")
        self.setFixedSize(400, 320)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._current_model: str = ""
        self._current_model_size: str = ""
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # App title
        self.title_label = QLabel("local-whisper")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # Model display frame (shows current model)
        model_display_frame = QFrame()
        model_display_frame.setObjectName("modelDisplayFrame")
        model_display_layout = QVBoxLayout(model_display_frame)
        model_display_layout.setContentsMargins(15, 12, 15, 12)
        model_display_layout.setSpacing(2)
        
        # "Model:" label
        model_header = QLabel("Model")
        model_header.setObjectName("modelHeader")
        model_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        model_header_font = QFont("Segoe UI", 9)
        model_header.setFont(model_header_font)
        model_display_layout.addWidget(model_header)
        
        # Current model name display
        self.model_display_label = QLabel("No model selected")
        self.model_display_label.setObjectName("modelDisplayLabel")
        self.model_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        model_display_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        self.model_display_label.setFont(model_display_font)
        model_display_layout.addWidget(self.model_display_label)
        
        layout.addWidget(model_display_frame)
        
        # Models menu button
        self.models_button = QPushButton("Models")
        self.models_button.setObjectName("modelsButton")
        self.models_button.setFixedHeight(36)
        self.models_button.clicked.connect(self._on_models_button_clicked)
        layout.addWidget(self.models_button)
        
        # Progress bar for loading model into memory (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Loading model...")
        layout.addWidget(self.progress_bar)
        
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
                padding: 5px;
            }
            #modelDisplayFrame {
                background-color: #16213e;
                border-radius: 8px;
                border: 1px solid #0f3460;
            }
            #modelHeader {
                color: #666677;
                background-color: transparent;
            }
            #modelDisplayLabel {
                color: #00d4aa;
                background-color: transparent;
            }
            #modelsButton {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #1a4a7a;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            #modelsButton:hover {
                background-color: #1a4a7a;
                border-color: #00d4aa;
            }
            #modelsButton:disabled {
                background-color: #0a1628;
                color: #555566;
                border-color: #0f3460;
            }
            #progressBar {
                background-color: #0f3460;
                border: 1px solid #1a4a7a;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            #progressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
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
    
    def _on_models_button_clicked(self) -> None:
        """Handle Models button click."""
        self.open_model_selector.emit()
    
    def set_current_model(self, model_name: str, model_size: str = "") -> None:
        """
        Set and display the currently selected model.
        
        Args:
            model_name: Name of the model (e.g., "large-v3")
            model_size: Size of the model (e.g., "~3 GB")
        """
        self._current_model = model_name
        self._current_model_size = model_size
        
        if model_name:
            if model_size:
                self.model_display_label.setText(f"{model_name} ({model_size})")
            else:
                self.model_display_label.setText(model_name)
            self.model_display_label.setStyleSheet(
                "color: #00d4aa; background-color: transparent;"
            )
        else:
            self.model_display_label.setText("No model selected")
            self.model_display_label.setStyleSheet(
                "color: #888899; background-color: transparent;"
            )
    
    def get_current_model(self) -> str:
        """Get the currently displayed model name."""
        return self._current_model
    
    def set_models_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Models button."""
        self.models_button.setEnabled(enabled)
    
    def show_loading_progress(self, visible: bool, message: str = "Loading model...") -> None:
        """
        Show or hide the loading progress indicator.
        
        Args:
            visible: Whether to show the progress bar
            message: Message to display
        """
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setFormat(message)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
    
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
