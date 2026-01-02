"""Entry point for Local Whisper application."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .app import LocalWhisperApp, AppState
from .transcriber import Transcriber
from .ui.main_window import MainWindow
from .ui.model_selector import ModelSelectorDialog
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
    
    # Model selector dialog (created on demand)
    model_selector: ModelSelectorDialog | None = None
    
    def get_model_size(model_name: str) -> str:
        """Get the size string for a model."""
        for model in Transcriber.get_available_models():
            if model['name'] == model_name:
                return model['size']
        return ""
    
    # Set initial model display
    if controller.selected_model:
        window.set_current_model(
            controller.selected_model, 
            get_model_size(controller.selected_model)
        )
    else:
        window.set_current_model("", "")
    
    # Connect signals
    def on_state_changed(state: AppState, message: str):
        """Handle state changes."""
        is_recording = state == AppState.RECORDING
        window.set_status(message, is_recording=is_recording)
        tray.set_recording(is_recording)
        
        # Enable/disable models button based on state
        can_open_models = state in (AppState.IDLE, AppState.NO_MODEL, AppState.ERROR)
        window.set_models_button_enabled(can_open_models)
        
        # Show loading state with progress indicator
        if state == AppState.LOADING:
            window.set_loading(message)
            window.show_loading_progress(True, message)
        else:
            window.show_loading_progress(False)
    
    def on_error(message: str):
        """Handle errors."""
        window.set_status(f"Error: {message}", is_recording=False)
        tray.show_message("local-whisper", message, tray.MessageIcon.Warning)
    
    def on_download_progress(model_name: str, progress: float, message: str):
        """Handle download progress updates - route to model selector."""
        nonlocal model_selector
        if model_selector and model_selector.isVisible():
            model_selector.update_download_progress(model_name, progress, message)
    
    def on_download_complete(model_name: str):
        """Handle download completion."""
        nonlocal model_selector
        if model_selector and model_selector.isVisible():
            model_selector.download_complete(model_name)
    
    def on_model_ready(model_name: str):
        """Handle model loaded successfully."""
        # Update main window model display
        window.set_current_model(model_name, get_model_size(model_name))
    
    def on_open_model_selector():
        """Handle opening the model selector dialog."""
        nonlocal model_selector
        
        # Create new dialog each time to refresh model states
        model_selector = ModelSelectorDialog(
            current_model=controller.selected_model,
            parent=window
        )
        
        def on_model_selected(model_name: str):
            """Handle model selection from dialog."""
            controller.select_model(model_name)
        
        def on_download_requested(model_name: str):
            """Handle download request from dialog."""
            model_selector.set_downloading(model_name, True)
            controller.start_download(model_name)
        
        model_selector.model_selected.connect(on_model_selected)
        model_selector.download_requested.connect(on_download_requested)
        
        model_selector.exec()
    
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
    controller.download_complete.connect(on_download_complete)
    controller.model_ready.connect(on_model_ready)
    
    window.open_model_selector.connect(on_open_model_selector)
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
