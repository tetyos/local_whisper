"""Entry point for Local Whisper application."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .app import LocalWhisperApp, AppState
from .transcriber import Transcriber
from .ui.main_window import MainWindow
from .ui.system_tray import SystemTray
from .ui.floating_indicator import FloatingIndicator


def main():
    """Main entry point."""
    # Redirect stdout/stderr to devnull if they are None (windowed app)
    # This prevents errors in libraries that try to print/log (like tqdm)
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

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
    
    # Create floating indicator
    floating = FloatingIndicator()
    
    # Create app controller
    controller = LocalWhisperApp()
    
    def get_model_info(model_name: str) -> dict:
        """Get the model info dict for a model."""
        for model in Transcriber.get_available_models():
            if model['name'] == model_name:
                return model
        return {}
    
    # Set initial model display
    if controller.selected_model:
        model_info = get_model_info(controller.selected_model)
        window.set_current_model(
            controller.selected_model,
            model_info.get('display_name', controller.selected_model)
        )
    else:
        window.set_current_model("", "")
    
    # Connect signals
    def on_state_changed(state: AppState, message: str):
        """Handle state changes."""
        is_recording = state == AppState.RECORDING
        is_transcribing = state == AppState.TRANSCRIBING
        window.set_status(message, is_recording=is_recording, is_transcribing=is_transcribing)
        tray.set_recording(is_recording)
        
        # Enable/disable models button based on state
        can_open_models = state in (AppState.IDLE, AppState.NO_MODEL, AppState.ERROR)
        window.set_models_button_enabled(can_open_models)
        
        # Show loading state
        if state == AppState.LOADING:
            window.set_loading(message)
        
        # Update floating indicator based on state
        if is_recording:
            floating.show_recording()
        elif is_transcribing:
            floating.show_transcribing()
        else:
            floating.hide_indicator()
    
    def on_transcription_progress(progress: float, elapsed: float, eta: float):
        """Handle transcription progress updates with ETA."""
        window.update_transcription_progress(progress, elapsed, eta)
        floating.update_transcription_progress(progress, elapsed, eta)
    
    def on_audio_level_changed(level: float):
        """Handle audio level updates from the recorder."""
        floating.update_audio_level(level)
    
    def on_error(message: str):
        """Handle errors."""
        window.set_status(f"Error: {message}", is_recording=False)
        tray.show_message("local-whisper", message, tray.MessageIcon.Warning)
    
    def on_download_progress(model_name: str, progress: float, message: str):
        """Handle download progress updates - route to main window."""
        window.update_download_progress(model_name, progress, message)
    
    def on_download_complete(model_name: str):
        """Handle download completion."""
        window.download_complete(model_name)
    
    def on_model_ready(model_name: str):
        """Handle model loaded successfully."""
        # Update main window model display
        model_info = get_model_info(model_name)
        window.set_current_model(model_name, model_info.get('display_name', model_name))
    
    def on_model_selected(model_name: str):
        """Handle model selection from window."""
        controller.select_model(model_name)
    
    def on_download_requested(model_name: str):
        """Handle download request from window."""
        window.set_downloading(model_name, True)
        controller.start_download(model_name)
    
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
    controller.transcription_progress.connect(on_transcription_progress)
    controller.audio_recorder.audio_level_changed.connect(on_audio_level_changed)
    
    window.model_selected.connect(on_model_selected)
    window.download_requested.connect(on_download_requested)
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
