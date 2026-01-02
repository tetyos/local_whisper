"""Entry point for Local Whisper application."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .app import LocalWhisperApp, AppState
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
    app.setApplicationName("local-whisper")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # Create main window
    window = MainWindow()
    
    # Create system tray
    tray = SystemTray()
    tray.show()
    
    # Create app controller
    controller = LocalWhisperApp()
    
    # Set initial model selection from settings
    window.set_selected_model(controller.selected_model)
    
    # Connect signals
    def on_state_changed(state: AppState, message: str):
        """Handle state changes."""
        is_recording = state == AppState.RECORDING
        window.set_status(message, is_recording=is_recording)
        tray.set_recording(is_recording)
        
        # Enable/disable model selection based on state
        can_change_model = state in (AppState.IDLE, AppState.NO_MODEL, AppState.ERROR)
        window.set_model_selection_enabled(can_change_model)
        
        # Show loading state
        if state == AppState.LOADING:
            window.set_loading(message)
        elif state == AppState.DOWNLOADING:
            window.set_loading(message)
    
    def on_error(message: str):
        """Handle errors."""
        window.set_status(f"Error: {message}", is_recording=False)
        tray.show_message("local-whisper", message, tray.MessageIcon.Warning)
    
    def on_download_progress(progress: float, message: str):
        """Handle download progress updates."""
        if progress < 0:
            window.hide_download_progress()
        else:
            window.show_download_progress(progress, message)
    
    def on_model_ready(model_name: str):
        """Handle model loaded successfully."""
        window.refresh_model_status()
        window.hide_download_progress()
    
    def on_model_changed(model_name: str):
        """Handle user selecting a different model."""
        controller.change_model(model_name)
    
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
            "local-whisper",
            "Application minimized to tray. Press Ctrl+Space to record.",
            tray.MessageIcon.Information,
            2000
        )
    
    # Connect all signals
    controller.state_changed.connect(on_state_changed)
    controller.error_occurred.connect(on_error)
    controller.download_progress.connect(on_download_progress)
    controller.model_ready.connect(on_model_ready)
    
    window.model_changed.connect(on_model_changed)
    window.close_to_tray.connect(on_close_to_tray)
    
    tray.show_window_requested.connect(on_show_window)
    tray.exit_requested.connect(on_exit)
    
    # Show window
    window.show()
    
    # Initialize controller (checks if model is downloaded, loads if available)
    controller.initialize()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
