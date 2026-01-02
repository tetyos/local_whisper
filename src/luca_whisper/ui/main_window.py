"""Main window UI for Luca Whisper."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent

from ..transcriber import Transcriber


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal emitted when window is closed (to minimize to tray)
    close_to_tray = pyqtSignal()
    # Signal emitted when user selects a different model
    model_changed = pyqtSignal(str)  # model_name
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("luca-whisper")
        self.setFixedSize(400, 320)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._current_model: str = ""  # Track current model to avoid duplicate signals
        self._setup_ui()
        self._apply_styles()
        self._populate_models()
    
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
        self.title_label = QLabel("luca-whisper")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # Model selection frame
        model_frame = QFrame()
        model_frame.setObjectName("modelFrame")
        model_layout = QHBoxLayout(model_frame)
        model_layout.setContentsMargins(15, 10, 15, 10)
        
        # Model label
        model_label = QLabel("Model:")
        model_label.setObjectName("modelLabel")
        model_font = QFont("Segoe UI", 11)
        model_label.setFont(model_font)
        model_layout.addWidget(model_label)
        
        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.setMinimumWidth(180)
        self.model_combo.currentIndexChanged.connect(self._on_model_selection_changed)
        model_layout.addWidget(self.model_combo)
        
        # Download status indicator
        self.download_status_label = QLabel("")
        self.download_status_label.setObjectName("downloadStatusLabel")
        self.download_status_label.setFixedWidth(80)
        model_layout.addWidget(self.download_status_label)
        
        layout.addWidget(model_frame)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - Downloading...")
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
            #modelFrame {
                background-color: #16213e;
                border-radius: 8px;
                border: 1px solid #0f3460;
            }
            #modelLabel {
                color: #aaaaaa;
                background-color: transparent;
            }
            #modelCombo {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #1a4a7a;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 25px;
            }
            #modelCombo:hover {
                border-color: #00d4aa;
            }
            #modelCombo::drop-down {
                border: none;
                width: 20px;
            }
            #modelCombo QAbstractItemView {
                background-color: #0f3460;
                color: #ffffff;
                selection-background-color: #1a4a7a;
                border: 1px solid #1a4a7a;
            }
            #downloadStatusLabel {
                background-color: transparent;
                font-size: 10px;
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
    
    def _populate_models(self) -> None:
        """Populate the model dropdown with available models."""
        models = Transcriber.get_available_models()
        for model in models:
            display_text = f"{model['name']} ({model['size']})"
            self.model_combo.addItem(display_text, model['name'])
    
    def _on_model_selection_changed(self, index: int) -> None:
        """Handle model selection change."""
        if index >= 0:
            model_name = self.model_combo.itemData(index)
            self._update_download_status(model_name)
            # Only emit signal if model actually changed (avoid duplicates)
            if model_name != self._current_model:
                self._current_model = model_name
                self.model_changed.emit(model_name)
    
    def _update_download_status(self, model_name: str) -> None:
        """Update the download status indicator for the selected model."""
        is_downloaded = Transcriber.is_model_downloaded(model_name)
        if is_downloaded:
            self.download_status_label.setText("✓ Ready")
            self.download_status_label.setStyleSheet(
                "color: #00d4aa; background-color: transparent;"
            )
        else:
            self.download_status_label.setText("⬇ Download")
            self.download_status_label.setStyleSheet(
                "color: #ffa502; background-color: transparent;"
            )
    
    def set_selected_model(self, model_name: str) -> None:
        """
        Set the selected model in the dropdown (programmatically, won't emit signal).
        
        Args:
            model_name: Name of the model to select
        """
        self._current_model = model_name
        # Block signals to prevent triggering model_changed when setting programmatically
        self.model_combo.blockSignals(True)
        for i in range(self.model_combo.count()):
            if self.model_combo.itemData(i) == model_name:
                self.model_combo.setCurrentIndex(i)
                break
        self.model_combo.blockSignals(False)
        self._update_download_status(model_name)
    
    def get_selected_model(self) -> str:
        """Get the currently selected model name."""
        return self.model_combo.currentData()
    
    def set_model_selection_enabled(self, enabled: bool) -> None:
        """Enable or disable model selection."""
        self.model_combo.setEnabled(enabled)
    
    def show_download_progress(self, progress: float, message: str = "") -> None:
        """
        Show download progress.
        
        Args:
            progress: Progress percentage (0-100), or -1 to hide
            message: Optional status message
        """
        if progress < 0:
            self.progress_bar.setVisible(False)
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(progress))
        if message:
            self.progress_bar.setFormat(f"%p% - {message}")
    
    def hide_download_progress(self) -> None:
        """Hide the download progress bar."""
        self.progress_bar.setVisible(False)
    
    def refresh_model_status(self) -> None:
        """Refresh the download status of the currently selected model."""
        model_name = self.get_selected_model()
        if model_name:
            self._update_download_status(model_name)
    
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
