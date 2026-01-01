"""Entry point for Luca Whisper application."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .app import LucaWhisperApp, AppState
from .ui.main_window import MainWindow
from .ui.system_tray import SystemTray


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("luca-whisper")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # Create main window
    window = MainWindow()
    
    # Create system tray
    tray = SystemTray()
    tray.show()
    
    # Create app controller
    controller = LucaWhisperApp()
    
    # Connect signals
    def on_state_changed(state: AppState, message: str):
        """Handle state changes."""
        is_recording = state == AppState.RECORDING
        window.set_status(message, is_recording=is_recording)
        tray.set_recording(is_recording)
    
    def on_error(message: str):
        """Handle errors."""
        window.set_status(f"Error: {message}", is_recording=False)
        tray.show_message("luca-whisper", message, tray.MessageIcon.Warning)
    
    def on_show_window():
        """Show the main window."""
        window.show()
        window.activateWindow()
        window.raise_()
    
    def on_exit():
        """Exit the application."""
        controller.shutdown()
        app.quit()
    
    def on_close_to_tray():
        """Handle window close (minimize to tray)."""
        tray.show_message(
            "luca-whisper",
            "Application minimized to tray. Press Ctrl+Space to record.",
            tray.MessageIcon.Information,
            2000
        )
    
    # Connect all signals
    controller.state_changed.connect(on_state_changed)
    controller.error_occurred.connect(on_error)
    tray.show_window_requested.connect(on_show_window)
    tray.exit_requested.connect(on_exit)
    window.close_to_tray.connect(on_close_to_tray)
    
    # Show window and initialize
    window.show()
    window.set_loading("Loading Whisper model (first run may take a moment)...")
    
    # Initialize controller (loads model in background)
    controller.initialize()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

