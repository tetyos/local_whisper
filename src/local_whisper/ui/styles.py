"""Shared styles for Local Whisper UI."""

# Color palette
COLORS = {
    "background": "#1a1a2e",
    "surface": "#16213e",
    "border": "#0f3460",
    "border_hover": "#1a4a7a",
    "accent": "#00d4aa",
    "accent_hover": "#00e6b8",
    "text": "#eaeaea",
    "text_muted": "#888899",
    "text_disabled": "#555566",
    "recording": "#ff4757",
    "loading": "#ffa502",
}

# Base application styles
BASE_STYLES = f"""
    QMainWindow {{
        background-color: {COLORS["background"]};
    }}
    QWidget {{
        background-color: {COLORS["background"]};
        color: {COLORS["text"]};
    }}
"""

# Main view styles
MAIN_VIEW_STYLES = f"""
    #titleLabel {{
        color: {COLORS["accent"]};
        padding: 5px;
    }}
    #modelDisplayFrame {{
        background-color: {COLORS["surface"]};
        border-radius: 8px;
        border: 1px solid {COLORS["border"]};
    }}
    #modelHeader {{
        color: #666677;
        background-color: transparent;
    }}
    #modelDisplayLabel {{
        color: {COLORS["accent"]};
        background-color: transparent;
    }}
    #modelsButton {{
        background-color: {COLORS["border"]};
        color: #ffffff;
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }}
    #modelsButton:hover {{
        background-color: {COLORS["border_hover"]};
        border-color: {COLORS["accent"]};
    }}
    #modelsButton:disabled {{
        background-color: #0a1628;
        color: {COLORS["text_disabled"]};
        border-color: {COLORS["border"]};
    }}
    #statusFrame {{
        background-color: {COLORS["surface"]};
        border-radius: 12px;
        border: 1px solid {COLORS["border"]};
    }}
    #statusLabel {{
        color: #ffffff;
        background-color: transparent;
    }}
    #hotkeyLabel {{
        color: {COLORS["text_muted"]};
        background-color: transparent;
    }}
    #transcriptionProgressBar {{
        background-color: {COLORS["border"]};
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 4px;
        text-align: center;
        color: #ffffff;
        font-size: 11px;
    }}
    #transcriptionProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        border-radius: 3px;
    }}
    #etaLabel {{
        color: {COLORS["text_muted"]};
        background-color: transparent;
        font-size: 11px;
        margin-top: 2px;
    }}
"""

# Model selector view styles
MODEL_SELECTOR_STYLES = f"""
    #dialogTitle {{
        color: {COLORS["accent"]};
    }}
    #backButton {{
        background-color: {COLORS["surface"]};
        color: #aaaaaa;
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 5px 10px;
    }}
    #backButton:hover {{
        background-color: {COLORS["border_hover"]};
        color: #ffffff;
    }}
    #modelScrollArea {{
        background-color: {COLORS["background"]};
        border: none;
    }}
    #modelScrollArea QScrollBar:vertical {{
        background-color: {COLORS["surface"]};
        width: 10px;
        border-radius: 5px;
    }}
    #modelScrollArea QScrollBar::handle:vertical {{
        background-color: {COLORS["border"]};
        border-radius: 5px;
        min-height: 20px;
    }}
    #modelScrollArea QScrollBar::handle:vertical:hover {{
        background-color: {COLORS["border_hover"]};
    }}
    #modelName {{
        color: #ffffff;
    }}
    #modelSize {{
        color: {COLORS["text_muted"]};
    }}
    #modelDescription {{
        color: {COLORS["text_muted"]};
    }}
    #downloadedLabel {{
        color: {COLORS["accent"]};
        font-weight: bold;
    }}
    #notDownloadedLabel {{
        color: #666677;
        font-size: 9px;
    }}
    #downloadButton {{
        background-color: {COLORS["border"]};
        color: #ffffff;
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 4px;
        padding: 5px 10px;
    }}
    #downloadButton:hover {{
        background-color: {COLORS["border_hover"]};
        border-color: {COLORS["accent"]};
    }}
    #downloadButton:disabled {{
        background-color: #0a1628;
        color: {COLORS["text_disabled"]};
        border-color: {COLORS["border"]};
    }}
    #cardProgressBar {{
        background-color: {COLORS["border"]};
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 4px;
        text-align: center;
        color: #ffffff;
    }}
    #cardProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        border-radius: 3px;
    }}
    #globalProgressBar {{
        background-color: {COLORS["border"]};
        border: 1px solid {COLORS["border_hover"]};
        border-radius: 4px;
        text-align: center;
        color: #ffffff;
        font-size: 11px;
    }}
    #globalProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        border-radius: 3px;
    }}
    #useButton {{
        background-color: {COLORS["accent"]};
        color: {COLORS["background"]};
        border: none;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
    }}
    #useButton:hover {{
        background-color: {COLORS["accent_hover"]};
    }}
    #useButton:disabled {{
        background-color: {COLORS["border"]};
        color: {COLORS["text_disabled"]};
    }}
    QRadioButton {{
        color: #ffffff;
    }}
    QRadioButton::indicator {{
        width: 16px;
        height: 16px;
    }}
    QRadioButton::indicator:unchecked {{
        border: 2px solid {COLORS["border"]};
        border-radius: 9px;
        background-color: {COLORS["surface"]};
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {COLORS["accent"]};
        border-radius: 9px;
        background-color: {COLORS["accent"]};
    }}
"""

# Model card styles
MODEL_CARD_SELECTED_STYLE = f"""
    #modelCard {{
        background-color: {COLORS["border_hover"]};
        border: 2px solid {COLORS["accent"]};
        border-radius: 8px;
    }}
"""

MODEL_CARD_UNSELECTED_STYLE = f"""
    #modelCard {{
        background-color: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}
    #modelCard:hover {{
        border-color: {COLORS["border_hover"]};
    }}
"""


def get_all_styles() -> str:
    """Get all combined styles for the application."""
    return BASE_STYLES + MAIN_VIEW_STYLES + MODEL_SELECTOR_STYLES

