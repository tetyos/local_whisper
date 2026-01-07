"""Model selector view for Local Whisper."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QButtonGroup, QRadioButton,
    QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QFont, QPainter, QPixmap, QColor, QPen, QIcon, QPolygonF

from ..transcriber import Transcriber
from .styles import MODEL_CARD_SELECTED_STYLE, MODEL_CARD_UNSELECTED_STYLE


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
    
    def _create_download_icon(self) -> QIcon:
        """Create a custom circled download arrow icon."""
        size = 20
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor("#ffffff")
        
        # Draw circle
        pen = QPen(color, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(1, 1, size-2, size-2)
        
        # Draw arrow
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        
        # Arrow shaft
        center_x = size / 2
        painter.drawRect(int(center_x - 1.5), 5, 3, 6)
        
        # Arrow head
        arrow_head = QPolygonF([
            QPointF(center_x - 4, 11),
            QPointF(center_x + 4, 11),
            QPointF(center_x, 15)
        ])
        painter.drawPolygon(arrow_head)
        
        painter.end()
        return QIcon(pixmap)

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
        
        # Model display name
        name_label = QLabel(f"{self.model_display_name}")
        name_label.setObjectName("modelName")
        name_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        name_label.setFont(name_font)
        top_row.addWidget(name_label)
        
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
            self.download_button.setIcon(self._create_download_icon())
            self.download_button.setFixedWidth(105)
            self.download_button.clicked.connect(self._on_download_clicked)
            self.status_label = None
            top_row.addWidget(self.download_button)
        
        layout.addLayout(top_row)
        
        # Description row
        desc_layout = QHBoxLayout()
        desc_layout.setContentsMargins(28, 0, 0, 0)
        desc_layout.setSpacing(10)
        
        desc_label = QLabel(self.model_description)
        desc_label.setObjectName("modelDescription")
        desc_font = QFont("Segoe UI", 9)
        desc_label.setFont(desc_font)
        desc_layout.addWidget(desc_label)
        
        size_label = QLabel(f"({self.model_size})")
        size_label.setObjectName("modelSize")
        size_font = QFont("Segoe UI", 10)
        size_label.setFont(size_font)
        desc_layout.addWidget(size_label)
        
        desc_layout.addStretch()
        
        layout.addLayout(desc_layout)
        
        self._update_style()
    
    def _update_style(self) -> None:
        """Update card style based on selection state."""
        if self.radio_button.isChecked():
            self.setStyleSheet(MODEL_CARD_SELECTED_STYLE)
        else:
            self.setStyleSheet(MODEL_CARD_UNSELECTED_STYLE)
    
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
            self.status_label = QLabel("Downloaded")
            self.status_label.setObjectName("downloadedLabel")
            top_layout = self.layout().itemAt(0).layout()
            top_layout.addWidget(self.status_label)
    
    def is_downloaded(self) -> bool:
        """Check if this model is downloaded."""
        return self._is_downloaded
    
    def set_selected(self, selected: bool) -> None:
        """Set the selection state."""
        self.radio_button.setChecked(selected)


class ModelSelectorView(QWidget):
    """View for selecting and downloading models."""
    
    # Signal emitted when user clicks back button
    back_requested = pyqtSignal()
    # Signal emitted when user selects a model to use
    model_selected = pyqtSignal(str)  # model_name
    # Signal emitted when user requests a download
    download_requested = pyqtSignal(str)  # model_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_model_name: str = ""
        self._selected_model: str = ""
        self._is_downloading = False
        self._downloading_model = ""
        self._model_cards: dict[str, ModelCard] = {}
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the model selector view."""
        layout = QVBoxLayout(self)
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
        
        # Global progress bar at bottom (hidden by default)
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
        
        self._update_use_button_state()
    
    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        if not self._is_downloading:
            self.back_requested.emit()
    
    def _on_model_card_selected(self, model_name: str) -> None:
        """Handle model selection change."""
        self._selected_model = model_name
        self._update_use_button_state()
    
    def _on_download_requested(self, model_name: str) -> None:
        """Handle download button click."""
        self.download_requested.emit(model_name)
    
    def _on_use_clicked(self) -> None:
        """Handle use button click."""
        if self._selected_model and self._model_cards[self._selected_model].is_downloaded():
            self.model_selected.emit(self._selected_model)
    
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
    
    def set_current_model(self, model_name: str) -> None:
        """Set the current model and update selection state."""
        self._current_model_name = model_name
        self._selected_model = model_name
        for name, card in self._model_cards.items():
            card.set_selected(name == model_name)
        self._update_use_button_state()
    
    def get_selected_model(self) -> str:
        """Get the currently selected model name."""
        return self._selected_model
    
    def set_downloading(self, model_name: str, is_downloading: bool) -> None:
        """Set the downloading state."""
        self._is_downloading = is_downloading
        self._downloading_model = model_name if is_downloading else ""
        
        # Disable/enable all download buttons
        for card in self._model_cards.values():
            card.set_download_enabled(not is_downloading)
        
        # Disable back button during download
        self.back_button.setEnabled(not is_downloading)
        
        self._update_use_button_state()
    
    def update_download_progress(self, model_name: str, progress: float, message: str) -> None:
        """Update download progress in the global progress bar."""
        self.global_progress_bar.setVisible(True)
        self.global_progress_bar.setValue(int(progress))
        if message:
            self.global_progress_bar.setFormat(message)
        else:
            self.global_progress_bar.setFormat(f"{int(progress)}%")
    
    def download_complete(self, model_name: str) -> None:
        """Mark a model as downloaded."""
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
    
    def refresh_selection(self, current_model: str) -> None:
        """Refresh the view when shown, syncing with current model."""
        self._selected_model = current_model
        for name, card in self._model_cards.items():
            card.set_selected(name == current_model)
        self._update_use_button_state()

