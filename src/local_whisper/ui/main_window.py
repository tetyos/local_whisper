"""Main window UI for Local Whisper."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QStackedWidget, QScrollArea, QButtonGroup, QRadioButton,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent

from ..transcriber import Transcriber


class ModelCard(QFrame):
    """A card widget displaying a single model with its details and actions."""
    
    download_requested = pyqtSignal(str)  # model_name
    selected = pyqtSignal(str)  # model_name
    
    def __init__(self, model_info: dict, is_current: bool = False, parent=None):
        super().__init__(parent)
        self.model_name = model_info['name']
        self.model_display_name = model_info.get('display_name', model_info['name'])
        self.model_size = model_info['size']
        self.model_description = model_info['description']
        self._is_downloaded = Transcriber.is_model_downloaded(self.model_name)
        self._is_current = is_current
        
        self.setObjectName("modelCard")
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)
        
        # Top row: radio button, model name, size, and download button
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Radio button for selection
        self.radio_button = QRadioButton()
        self.radio_button.setObjectName("modelRadio")
        self.radio_button.setChecked(self._is_current)
        self.radio_button.toggled.connect(self._on_radio_toggled)
        top_row.addWidget(self.radio_button)
        
        # Model display name and size
        name_label = QLabel(f"{self.model_display_name}")
        name_label.setObjectName("modelName")
        name_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        name_label.setFont(name_font)
        top_row.addWidget(name_label)
        
        size_label = QLabel(f"({self.model_size})")
        size_label.setObjectName("modelSize")
        size_font = QFont("Segoe UI", 10)
        size_label.setFont(size_font)
        top_row.addWidget(size_label)
        
        top_row.addStretch()
        
        # Download button or downloaded label
        if self._is_downloaded:
            self.status_label = QLabel("Downloaded")
            self.status_label.setObjectName("downloadedLabel")
            self.download_button = None
            top_row.addWidget(self.status_label)
        else:
            self.download_button = QPushButton("Download")
            self.download_button.setObjectName("downloadButton")
            self.download_button.setFixedWidth(90)
            self.download_button.clicked.connect(self._on_download_clicked)
            self.status_label = None
            top_row.addWidget(self.download_button)
        
        layout.addLayout(top_row)
        
        # Description row
        desc_layout = QHBoxLayout()
        desc_layout.setContentsMargins(28, 0, 0, 0)  # Indent to align with text after radio
        
        desc_label = QLabel(self.model_description)
        desc_label.setObjectName("modelDescription")
        desc_font = QFont("Segoe UI", 9)
        desc_label.setFont(desc_font)
        desc_layout.addWidget(desc_label)
        desc_layout.addStretch()
        
        # Status text for not downloaded
        if not self._is_downloaded:
            not_downloaded_label = QLabel("Not downloaded")
            not_downloaded_label.setObjectName("notDownloadedLabel")
            desc_layout.addWidget(not_downloaded_label)
        
        layout.addLayout(desc_layout)
        
        self._update_style()
    
    def _update_style(self) -> None:
        """Update card style based on selection state."""
        if self.radio_button.isChecked():
            self.setStyleSheet("""
                #modelCard {
                    background-color: #1a4a7a;
                    border: 2px solid #00d4aa;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                #modelCard {
                    background-color: #16213e;
                    border: 1px solid #0f3460;
                    border-radius: 8px;
                }
                #modelCard:hover {
                    border-color: #1a4a7a;
                }
            """)
    
    def _on_radio_toggled(self, checked: bool) -> None:
        """Handle radio button toggle."""
        self._update_style()
        if checked:
            self.selected.emit(self.model_name)
    
    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        self.download_requested.emit(self.model_name)
    
    def set_download_enabled(self, enabled: bool) -> None:
        """Enable or disable the download button."""
        if self.download_button:
            self.download_button.setEnabled(enabled)
    
    def mark_as_downloaded(self) -> None:
        """Update the card to show downloaded state."""
        self._is_downloaded = True
        if self.download_button:
            self.download_button.setVisible(False)
            # Add downloaded label
            self.status_label = QLabel("Downloaded")
            self.status_label.setObjectName("downloadedLabel")
            # Find the top row layout and add the label
            top_layout = self.layout().itemAt(0).layout()
            top_layout.addWidget(self.status_label)
        
        # Remove "Not downloaded" label if present
        desc_layout = self.layout().itemAt(1).layout()
        for i in range(desc_layout.count()):
            item = desc_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.objectName() == "notDownloadedLabel":
                    widget.setVisible(False)
    
    def is_downloaded(self) -> bool:
        """Check if this model is downloaded."""
        return self._is_downloaded
    
    def set_selected(self, selected: bool) -> None:
        """Set the selection state."""
        self.radio_button.setChecked(selected)


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signal emitted when window is closed (to minimize to tray)
    close_to_tray = pyqtSignal()
    # Signal emitted when user selects a model
    model_selected = pyqtSignal(str)  # model_name
    # Signal emitted when user requests a download
    download_requested = pyqtSignal(str)  # model_name
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("local-whisper")
        # Set initial size larger for better model selector view
        self.resize(400, 400)
        # Set minimum size to prevent window from becoming too small
        self.setMinimumSize(400, 400)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._current_model_name: str = ""  # Internal model name (e.g., "small")
        self._current_model_display: str = ""  # Display name (e.g., "OpenAI Whisper Small")
        self._selected_model: str = ""  # Internal model name of selected model in selector
        self._is_downloading = False
        self._downloading_model = ""
        self._model_cards: dict[str, ModelCard] = {}  # Keyed by internal model name
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget with stacked layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Stacked widget to switch between main view and model selector
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Create main view
        self._setup_main_view()
        
        # Create model selector view
        self._setup_model_selector_view()
        
        # Start with main view
        self.stacked_widget.setCurrentIndex(0)
    
    def _setup_main_view(self) -> None:
        """Set up the main view."""
        main_view = QWidget()
        layout = QVBoxLayout(main_view)
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
        self.models_button.clicked.connect(self._on_models_button_clicked)
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
        
        self.stacked_widget.addWidget(main_view)
    
    def _setup_model_selector_view(self) -> None:
        """Set up the model selector view."""
        model_view = QWidget()
        layout = QVBoxLayout(model_view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header with back button and title
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("backButton")
        self.back_button.setFixedWidth(80)
        self.back_button.clicked.connect(self._on_back_clicked)
        header_layout.addWidget(self.back_button)
        
        header_layout.addStretch()
        
        selector_title_label = QLabel("Select Model")
        selector_title_label.setObjectName("dialogTitle")
        selector_title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        selector_title_label.setFont(selector_title_font)
        header_layout.addWidget(selector_title_label)
        
        header_layout.addStretch()
        
        # Spacer to balance the back button
        spacer = QWidget()
        spacer.setFixedWidth(80)
        header_layout.addWidget(spacer)
        
        layout.addLayout(header_layout)
        
        # Scrollable model list
        scroll_area = QScrollArea()
        scroll_area.setObjectName("modelScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)
        
        # Create button group for radio buttons
        self.button_group = QButtonGroup(self)
        
        # Create model cards
        models = Transcriber.get_available_models()
        for model in models:
            is_current = model['name'] == self._current_model_name
            card = ModelCard(model, is_current=is_current)
            card.download_requested.connect(self._on_download_requested)
            card.selected.connect(self._on_model_card_selected)
            self.button_group.addButton(card.radio_button)
            self._model_cards[model['name']] = card
            self.scroll_layout.addWidget(card)
        
        self.scroll_layout.addStretch()
        scroll_area.setWidget(self.scroll_content)
        layout.addWidget(scroll_area)
        
        # Global progress bar at bottom (hidden by default, shown during download)
        self.global_progress_bar = QProgressBar()
        self.global_progress_bar.setObjectName("globalProgressBar")
        self.global_progress_bar.setVisible(False)
        self.global_progress_bar.setTextVisible(True)
        self.global_progress_bar.setFixedHeight(24)
        layout.addWidget(self.global_progress_bar)
        
        # Bottom action button
        self.use_button = QPushButton("Use this model")
        self.use_button.setObjectName("useButton")
        self.use_button.setFixedHeight(40)
        self.use_button.clicked.connect(self._on_use_clicked)
        layout.addWidget(self.use_button)
        
        # Update button state
        self._update_use_button_state()
        
        self.stacked_widget.addWidget(model_view)
    
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
            #dialogTitle {
                color: #00d4aa;
            }
            #backButton {
                background-color: #16213e;
                color: #aaaaaa;
                border: 1px solid #0f3460;
                border-radius: 4px;
                padding: 5px 10px;
            }
            #backButton:hover {
                background-color: #1a4a7a;
                color: #ffffff;
            }
            #modelScrollArea {
                background-color: #1a1a2e;
                border: none;
            }
            #modelScrollArea QScrollBar:vertical {
                background-color: #16213e;
                width: 10px;
                border-radius: 5px;
            }
            #modelScrollArea QScrollBar::handle:vertical {
                background-color: #0f3460;
                border-radius: 5px;
                min-height: 20px;
            }
            #modelScrollArea QScrollBar::handle:vertical:hover {
                background-color: #1a4a7a;
            }
            #modelName {
                color: #ffffff;
            }
            #modelSize {
                color: #888899;
            }
            #modelDescription {
                color: #888899;
            }
            #downloadedLabel {
                color: #00d4aa;
                font-weight: bold;
            }
            #notDownloadedLabel {
                color: #666677;
                font-size: 9px;
            }
            #downloadButton {
                background-color: #0f3460;
                color: #ffffff;
                border: 1px solid #1a4a7a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            #downloadButton:hover {
                background-color: #1a4a7a;
                border-color: #00d4aa;
            }
            #downloadButton:disabled {
                background-color: #0a1628;
                color: #555566;
                border-color: #0f3460;
            }
            #cardProgressBar {
                background-color: #0f3460;
                border: 1px solid #1a4a7a;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            #cardProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
            #globalProgressBar {
                background-color: #0f3460;
                border: 1px solid #1a4a7a;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-size: 11px;
            }
            #globalProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
            #useButton {
                background-color: #00d4aa;
                color: #1a1a2e;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            #useButton:hover {
                background-color: #00e6b8;
            }
            #useButton:disabled {
                background-color: #0f3460;
                color: #555566;
            }
            QRadioButton {
                color: #ffffff;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #0f3460;
                border-radius: 9px;
                background-color: #16213e;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #00d4aa;
                border-radius: 9px;
                background-color: #00d4aa;
            }
        """)
    
    def _on_models_button_clicked(self) -> None:
        """Handle Models button click - switch to model selector view."""
        # Update model cards to reflect current selection
        self._selected_model = self._current_model_name
        for name, card in self._model_cards.items():
            card.set_selected(name == self._current_model_name)
        self._update_use_button_state()
        self.stacked_widget.setCurrentIndex(1)
    
    def _on_back_clicked(self) -> None:
        """Handle back button click - return to main view."""
        if not self._is_downloading:
            self.stacked_widget.setCurrentIndex(0)
    
    def _on_model_card_selected(self, model_name: str) -> None:
        """Handle model selection change in the model selector."""
        self._selected_model = model_name
        self._update_use_button_state()
    
    def _on_download_requested(self, model_name: str) -> None:
        """Handle download button click."""
        self.download_requested.emit(model_name)
    
    def _on_use_clicked(self) -> None:
        """Handle use button click."""
        if self._selected_model and self._model_cards[self._selected_model].is_downloaded():
            self.model_selected.emit(self._selected_model)
            self.stacked_widget.setCurrentIndex(0)
    
    def _update_use_button_state(self) -> None:
        """Update the use button enabled state."""
        if not self._selected_model:
            self.use_button.setEnabled(False)
            self.use_button.setText("Select a model")
        elif self._is_downloading:
            self.use_button.setEnabled(False)
            self.use_button.setText("Downloading...")
        elif not self._model_cards[self._selected_model].is_downloaded():
            self.use_button.setEnabled(False)
            self.use_button.setText("Download model first")
        else:
            self.use_button.setEnabled(True)
            self.use_button.setText("Use this model")
    
    def set_current_model(self, model_name: str, display_name: str) -> None:
        """
        Set and display the currently selected model.
        
        Args:
            model_name: Internal model name (e.g., "small")
            display_name: Display name of the model (e.g., "OpenAI Whisper Small")
        """
        self._current_model_name = model_name
        self._current_model_display = display_name
        
        if display_name:
            self.model_display_label.setText(display_name)
            self.model_display_label.setStyleSheet(
                "color: #00d4aa; background-color: transparent;"
            )
        else:
            self.model_display_label.setText("No model selected")
            self.model_display_label.setStyleSheet(
                "color: #888899; background-color: transparent;"
            )
    
    def get_current_model(self) -> str:
        """Get the currently selected internal model name."""
        return self._current_model_name
    
    def set_models_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Models button."""
        self.models_button.setEnabled(enabled)
    
    def set_downloading(self, model_name: str, is_downloading: bool) -> None:
        """Set the downloading state."""
        self._is_downloading = is_downloading
        self._downloading_model = model_name if is_downloading else ""
        
        # Disable/enable all download buttons
        for name, card in self._model_cards.items():
            card.set_download_enabled(not is_downloading)
        
        # Disable back button during download
        self.back_button.setEnabled(not is_downloading)
        
        self._update_use_button_state()
    
    def update_download_progress(self, model_name: str, progress: float, message: str) -> None:
        """Update download progress in the global progress bar."""
        self.global_progress_bar.setVisible(True)
        self.global_progress_bar.setValue(int(progress))
        if message:
            # Show detailed file info (e.g., "Downloading model.bin (1.2 GB/1.5 GB)")
            self.global_progress_bar.setFormat(message)
        else:
            self.global_progress_bar.setFormat(f"{int(progress)}%")
    
    def download_complete(self, model_name: str) -> None:
        """Mark a model as downloaded."""
        # Hide global progress bar
        self.global_progress_bar.setVisible(False)
        
        if model_name in self._model_cards:
            self._model_cards[model_name].mark_as_downloaded()
        
        self._is_downloading = False
        self._downloading_model = ""
        
        # Re-enable all download buttons
        for card in self._model_cards.values():
            card.set_download_enabled(True)
        
        # Re-enable back button
        self.back_button.setEnabled(True)
        
        self._update_use_button_state()
    
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
