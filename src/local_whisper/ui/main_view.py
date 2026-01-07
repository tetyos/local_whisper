"""Main status view for Local Whisper."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .styles import COLORS


class MainView(QWidget):
    """Main view showing status, model info, and hotkey hints."""
    
    # Signal emitted when user clicks the models button
    models_button_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the main view."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # App title
        self.title_label = QLabel("local-whisper")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        # Models menu button
        self.models_button = QPushButton("Select model")
        self.models_button.setObjectName("modelsButton")
        self.models_button.setFixedHeight(36)
        self.models_button.clicked.connect(self.models_button_clicked.emit)
        layout.addWidget(self.models_button)
        
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
        
        # Status frame
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 15, 20, 15)
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        status_font = QFont("Segoe UI", 12)
        self.status_label.setFont(status_font)
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        
        # Transcription progress bar (hidden by default)
        self.transcription_progress_bar = QProgressBar()
        self.transcription_progress_bar.setObjectName("transcriptionProgressBar")
        self.transcription_progress_bar.setVisible(False)
        self.transcription_progress_bar.setTextVisible(True)
        self.transcription_progress_bar.setFixedHeight(20)
        self.transcription_progress_bar.setFormat("Transcribing...")
        status_layout.addWidget(self.transcription_progress_bar)
        
        # ETA label (hidden by default)
        self.eta_label = QLabel("")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eta_label.setObjectName("etaLabel")
        eta_font = QFont("Segoe UI", 10)
        self.eta_label.setFont(eta_font)
        self.eta_label.setVisible(False)
        status_layout.addWidget(self.eta_label)
        
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
    
    def set_model_display(self, display_name: str) -> None:
        """Set the model display label."""
        if display_name:
            self.model_display_label.setText(display_name)
            self.model_display_label.setStyleSheet(
                f"color: {COLORS['accent']}; background-color: transparent;"
            )
        else:
            self.model_display_label.setText("No model selected")
            self.model_display_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; background-color: transparent;"
            )
    
    def set_models_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Models button."""
        self.models_button.setEnabled(enabled)
    
    def set_status(self, status: str, is_recording: bool = False, is_transcribing: bool = False) -> None:
        """
        Update the status display.
        
        Args:
            status: Status text to display
            is_recording: Whether currently recording (changes styling)
            is_transcribing: Whether currently transcribing (shows progress bar)
        """
        self.status_label.setText(status)
        
        # Show/hide transcription progress UI based on state
        if not is_transcribing:
            self.transcription_progress_bar.setVisible(False)
            self.eta_label.setVisible(False)
        
        if is_recording:
            self.status_label.setStyleSheet(f"""
                color: {COLORS["recording"]};
                background-color: transparent;
                font-weight: bold;
            """)
        else:
            self.status_label.setStyleSheet("""
                color: #ffffff;
                background-color: transparent;
                font-weight: normal;
            """)
    
    def update_transcription_progress(self, progress: float, elapsed: float, eta: float) -> None:
        """
        Update transcription progress display with ETA.
        
        Args:
            progress: Transcription progress (0-100)
            elapsed: Elapsed time in seconds
            eta: Estimated time remaining in seconds
        """
        self.transcription_progress_bar.setVisible(True)
        self.eta_label.setVisible(True)
        
        self.transcription_progress_bar.setValue(int(progress))
        self.transcription_progress_bar.setFormat(f"Transcribing... {int(progress)}%")
        
        if eta < 1 and progress < 100:
            self.eta_label.setText("Finishing up...")
        else:
            eta_text = self._format_time(eta)
            self.eta_label.setText(f"Estimated time remaining: {eta_text}")
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds into a human-readable string."""
        if seconds < 1:
            return "less than 1s"
        elif seconds < 60:
            return f"{int(seconds)}s"
        else:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
    
    def set_loading(self, message: str) -> None:
        """Show loading state."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            color: {COLORS["loading"]};
            background-color: transparent;
        """)

