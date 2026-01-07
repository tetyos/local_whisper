"""Main window UI for Local Whisper."""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent

from .styles import get_all_styles
from .main_view import MainView
from .model_selector_view import ModelSelectorView


class MainWindow(QMainWindow):
    """Main application window - coordinates between views."""
    
    # Signal emitted when window is closed (to minimize to tray)
    close_to_tray = pyqtSignal()
    # Signal emitted when user selects a model
    model_selected = pyqtSignal(str)  # model_name
    # Signal emitted when user requests a download
    download_requested = pyqtSignal(str)  # model_name
    
    # View indices
    VIEW_MAIN = 0
    VIEW_MODEL_SELECTOR = 1
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("local-whisper")
        self.resize(450, 450)
        self.setMinimumSize(450, 450)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._current_model_name: str = ""
        self._current_model_display: str = ""
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create views
        self.main_view = MainView()
        self.model_selector_view = ModelSelectorView()
        
        # Add views to stack
        self.stacked_widget.addWidget(self.main_view)
        self.stacked_widget.addWidget(self.model_selector_view)
        
        # Start with main view
        self.stacked_widget.setCurrentIndex(self.VIEW_MAIN)
    
    def _connect_signals(self) -> None:
        """Connect signals between views."""
        # Main view signals
        self.main_view.models_button_clicked.connect(self._show_model_selector)
        
        # Model selector signals
        self.model_selector_view.back_requested.connect(self._show_main_view)
        self.model_selector_view.model_selected.connect(self._on_model_selected)
        self.model_selector_view.download_requested.connect(self.download_requested.emit)
    
    def _apply_styles(self) -> None:
        """Apply CSS styles to the window."""
        self.setStyleSheet(get_all_styles())
    
    def _show_model_selector(self) -> None:
        """Switch to model selector view."""
        self.model_selector_view.refresh_selection(self._current_model_name)
        self.stacked_widget.setCurrentIndex(self.VIEW_MODEL_SELECTOR)
    
    def _show_main_view(self) -> None:
        """Switch to main view."""
        self.stacked_widget.setCurrentIndex(self.VIEW_MAIN)
        
        # Clear focus to prevent accidental button activation (e.g. when using hotkeys)
        if self.focusWidget():
            self.focusWidget().clearFocus()
    
    def _on_model_selected(self, model_name: str) -> None:
        """Handle model selection from selector view."""
        self.model_selected.emit(model_name)
        self._show_main_view()
    
    # -------------------------------------------------------------------------
    # Public API - delegated to appropriate views
    # -------------------------------------------------------------------------
    
    def set_current_model(self, model_name: str, display_name: str) -> None:
        """
        Set and display the currently selected model.
        
        Args:
            model_name: Internal model name (e.g., "small")
            display_name: Display name of the model (e.g., "OpenAI Whisper Small")
        """
        self._current_model_name = model_name
        self._current_model_display = display_name
        self.main_view.set_model_display(display_name)
        self.model_selector_view.set_current_model(model_name)
    
    def get_current_model(self) -> str:
        """Get the currently selected internal model name."""
        return self._current_model_name
    
    def set_models_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Models button."""
        self.main_view.set_models_button_enabled(enabled)
    
    def set_downloading(self, model_name: str, is_downloading: bool) -> None:
        """Set the downloading state."""
        self.model_selector_view.set_downloading(model_name, is_downloading)
    
    def update_download_progress(self, model_name: str, progress: float, message: str) -> None:
        """Update download progress in the model selector."""
        self.model_selector_view.update_download_progress(model_name, progress, message)
    
    def download_complete(self, model_name: str) -> None:
        """Mark a model as downloaded."""
        self.model_selector_view.download_complete(model_name)
    
    def set_status(self, status: str, is_recording: bool = False, is_transcribing: bool = False) -> None:
        """Update the status display."""
        self.main_view.set_status(status, is_recording, is_transcribing)
    
    def update_transcription_progress(self, progress: float, elapsed: float, eta: float) -> None:
        """Update transcription progress display with ETA."""
        self.main_view.update_transcription_progress(progress, elapsed, eta)
    
    def set_loading(self, message: str) -> None:
        """Show loading state."""
        self.main_view.set_loading(message)
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event - minimize to tray instead."""
        event.ignore()
        self.hide()
        self.close_to_tray.emit()
