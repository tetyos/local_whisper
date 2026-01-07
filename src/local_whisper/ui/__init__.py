"""UI components for Local Whisper."""

from .main_window import MainWindow
from .main_view import MainView
from .model_selector_view import ModelSelectorView, ModelCard
from .system_tray import SystemTray
from .floating_indicator import FloatingIndicator
from .styles import COLORS, get_all_styles

__all__ = [
    "MainWindow",
    "MainView",
    "ModelSelectorView",
    "ModelCard",
    "SystemTray",
    "FloatingIndicator",
    "COLORS",
    "get_all_styles",
]
