"""Main application class that coordinates all components."""

from enum import Enum, auto
from typing import Optional
import threading

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .audio_recorder import AudioRecorder
from .transcriber import Transcriber, is_model_downloaded, download_model
from .hotkey_handler import HotkeyHandler
from .text_output import TextOutput
from .settings import get_selected_model, set_selected_model


class AppState(Enum):
    """Application state machine states."""
    LOADING = auto()
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    TYPING = auto()
    DOWNLOADING = auto()
    NO_MODEL = auto()  # No model selected/downloaded
    ERROR = auto()


class LocalWhisperApp(QObject):
    """Main application controller."""
    
    # Signals for UI updates (thread-safe)
    state_changed = pyqtSignal(AppState, str)  # state, message
    error_occurred = pyqtSignal(str)  # error message
    download_progress = pyqtSignal(float, str)  # progress (0-100), message
    model_ready = pyqtSignal(str)  # model_name - emitted when model is loaded
    
    def __init__(self):
        super().__init__()
        
        # Load selected model from settings
        self._selected_model = get_selected_model()
        
        # Initialize components
        self.audio_recorder = AudioRecorder(sample_rate=16000)
        self.transcriber = Transcriber(model_size=self._selected_model, device="auto")
        self.hotkey_handler = HotkeyHandler(hotkey="ctrl+space")
        self.text_output = TextOutput(typing_interval=0.005)
        
        # State
        self._state = AppState.LOADING
        self._lock = threading.Lock()
        self._hotkey_registered = False
    
    @property
    def state(self) -> AppState:
        """Get current application state."""
        with self._lock:
            return self._state
    
    @state.setter
    def state(self, value: AppState) -> None:
        """Set application state."""
        with self._lock:
            self._state = value
    
    @property
    def selected_model(self) -> str:
        """Get the currently selected model name."""
        return self._selected_model
    
    def _register_hotkey(self) -> None:
        """Register the hotkey if not already registered."""
        if not self._hotkey_registered:
            self.hotkey_handler.register(self._on_hotkey_pressed)
            self._hotkey_registered = True
    
    def initialize(self) -> None:
        """Initialize the application (load model if available, register hotkey)."""
        self.state = AppState.LOADING
        
        # Register hotkey early so it's available
        self._register_hotkey()
        
        # Check if the selected model is downloaded
        if is_model_downloaded(self._selected_model):
            self.state_changed.emit(AppState.LOADING, f"Loading {self._selected_model} model...")
            self._load_model_async()
        else:
            # Model not downloaded - wait for user to trigger download
            self.state = AppState.NO_MODEL
            self.state_changed.emit(
                AppState.NO_MODEL, 
                f"Model '{self._selected_model}' not downloaded. Select a model to download."
            )
    
    def _load_model_async(self) -> None:
        """Load the model in a background thread."""
        def load_model():
            try:
                def on_progress(progress: float, message: str):
                    self.download_progress.emit(progress, message)
                
                self.transcriber.load_model(on_progress=on_progress)
                
                self.state = AppState.IDLE
                self.state_changed.emit(AppState.IDLE, "Ready")
                self.model_ready.emit(self._selected_model)
                
            except Exception as e:
                self.state = AppState.ERROR
                self.error_occurred.emit(f"Failed to load model: {str(e)}")
        
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()
    
    def change_model(self, model_name: str) -> None:
        """
        Change to a different model.
        
        Args:
            model_name: Name of the model to switch to
        """
        if model_name == self._selected_model and self.transcriber.is_loaded():
            # Same model, already loaded
            return
        
        # Don't allow model change while recording or transcribing
        current_state = self.state
        if current_state in (AppState.RECORDING, AppState.TRANSCRIBING, AppState.TYPING, AppState.DOWNLOADING):
            self.error_occurred.emit("Cannot change model while busy. Please wait.")
            return
        
        # Update selected model
        self._selected_model = model_name
        set_selected_model(model_name)
        self.transcriber.set_model_size(model_name)
        
        # Check if model is downloaded
        if is_model_downloaded(model_name):
            # Load the model
            self.state = AppState.LOADING
            self.state_changed.emit(AppState.LOADING, f"Loading {model_name} model...")
            self._load_model_async()
        else:
            # Need to download first
            self.state = AppState.DOWNLOADING
            self.state_changed.emit(AppState.DOWNLOADING, f"Downloading {model_name}...")
            self._download_and_load_model(model_name)
    
    def _download_and_load_model(self, model_name: str) -> None:
        """Download and load a model in background thread."""
        def download_and_load():
            try:
                def on_progress(progress: float, message: str):
                    self.download_progress.emit(progress, message)
                
                # Download the model
                download_model(model_name, on_progress=on_progress)
                
                # Now load it
                self.state = AppState.LOADING
                self.state_changed.emit(AppState.LOADING, f"Loading {model_name} model...")
                
                self.transcriber.load_model(on_progress=on_progress)
                
                self.state = AppState.IDLE
                self.state_changed.emit(AppState.IDLE, "Ready")
                self.model_ready.emit(model_name)
                self.download_progress.emit(-1, "")  # Hide progress
                
            except Exception as e:
                self.state = AppState.ERROR
                self.error_occurred.emit(f"Failed to download/load model: {str(e)}")
                self.download_progress.emit(-1, "")  # Hide progress
        
        thread = threading.Thread(target=download_and_load, daemon=True)
        thread.start()
    
    def _on_hotkey_pressed(self) -> None:
        """Handle hotkey press event."""
        current_state = self.state
        
        if current_state == AppState.IDLE:
            self._start_recording()
        elif current_state == AppState.RECORDING:
            self._stop_recording_and_transcribe()
        elif current_state == AppState.NO_MODEL:
            self.error_occurred.emit("No model loaded. Please select and download a model first.")
        # Ignore hotkey in other states (loading, transcribing, typing, downloading)
    
    def _start_recording(self) -> None:
        """Start audio recording."""
        if not self.transcriber.is_loaded():
            self.error_occurred.emit("Model not loaded. Please wait or select a model.")
            return
        
        try:
            self.audio_recorder.start_recording()
            self.state = AppState.RECORDING
            self.state_changed.emit(AppState.RECORDING, "🎤 Recording... Press Ctrl+Space to stop")
        except Exception as e:
            self.state = AppState.ERROR
            self.error_occurred.emit(f"Failed to start recording: {str(e)}")
            # Try to recover
            QTimer.singleShot(2000, self._recover_to_idle)
    
    def _stop_recording_and_transcribe(self) -> None:
        """Stop recording and transcribe the audio."""
        try:
            # Stop recording
            audio_data = self.audio_recorder.stop_recording()
            
            if len(audio_data) == 0:
                self.state = AppState.IDLE
                self.state_changed.emit(AppState.IDLE, "No audio recorded. Ready.")
                return
            
            self.state = AppState.TRANSCRIBING
            self.state_changed.emit(AppState.TRANSCRIBING, "Transcribing...")
            
            # Transcribe in background thread
            def transcribe_and_type():
                try:
                    text = self.transcriber.transcribe(audio_data)
                    
                    if text.strip():
                        self.state = AppState.TYPING
                        self.state_changed.emit(AppState.TYPING, "Typing...")
                        
                        # Type the text
                        self.text_output.type_text(text.strip())
                    
                    self.state = AppState.IDLE
                    self.state_changed.emit(AppState.IDLE, "Ready")
                    
                except Exception as e:
                    self.state = AppState.ERROR
                    self.error_occurred.emit(f"Transcription failed: {str(e)}")
                    QTimer.singleShot(2000, self._recover_to_idle)
            
            thread = threading.Thread(target=transcribe_and_type, daemon=True)
            thread.start()
            
        except Exception as e:
            self.state = AppState.ERROR
            self.error_occurred.emit(f"Failed to stop recording: {str(e)}")
            QTimer.singleShot(2000, self._recover_to_idle)
    
    def _recover_to_idle(self) -> None:
        """Recover to idle state after an error."""
        if self.transcriber.is_loaded():
            self.state = AppState.IDLE
            self.state_changed.emit(AppState.IDLE, "Ready")
        else:
            self.state = AppState.NO_MODEL
            self.state_changed.emit(AppState.NO_MODEL, "Select a model to continue.")
    
    def shutdown(self) -> None:
        """Shutdown the application and clean up resources."""
        # Unregister hotkey
        self.hotkey_handler.unregister()
        
        # Stop any ongoing recording
        if self.audio_recorder.is_recording():
            self.audio_recorder.stop_recording()
