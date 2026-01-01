"""Main application class that coordinates all components."""

from enum import Enum, auto
from typing import Optional
import threading

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .audio_recorder import AudioRecorder
from .transcriber import Transcriber
from .hotkey_handler import HotkeyHandler
from .text_output import TextOutput


class AppState(Enum):
    """Application state machine states."""
    LOADING = auto()
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    TYPING = auto()
    ERROR = auto()


class LucaWhisperApp(QObject):
    """Main application controller."""
    
    # Signals for UI updates (thread-safe)
    state_changed = pyqtSignal(AppState, str)  # state, message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.audio_recorder = AudioRecorder(sample_rate=16000)
        self.transcriber = Transcriber(model_size="base", device="auto")
        self.hotkey_handler = HotkeyHandler(hotkey="ctrl+space")
        self.text_output = TextOutput(typing_interval=0.005)
        
        # State
        self._state = AppState.LOADING
        self._lock = threading.Lock()
    
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
    
    def initialize(self) -> None:
        """Initialize the application (load model, register hotkey)."""
        self.state = AppState.LOADING
        self.state_changed.emit(AppState.LOADING, "Loading Whisper model...")
        
        # Load model in background thread
        def load_model():
            try:
                self.transcriber.load_model()
                
                # Register hotkey
                self.hotkey_handler.register(self._on_hotkey_pressed)
                
                self.state = AppState.IDLE
                self.state_changed.emit(AppState.IDLE, "Ready")
            except Exception as e:
                self.state = AppState.ERROR
                self.error_occurred.emit(f"Failed to load model: {str(e)}")
        
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()
    
    def _on_hotkey_pressed(self) -> None:
        """Handle hotkey press event."""
        current_state = self.state
        
        if current_state == AppState.IDLE:
            self._start_recording()
        elif current_state == AppState.RECORDING:
            self._stop_recording_and_transcribe()
        # Ignore hotkey in other states (loading, transcribing, typing)
    
    def _start_recording(self) -> None:
        """Start audio recording."""
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
        self.state = AppState.IDLE
        self.state_changed.emit(AppState.IDLE, "Ready")
    
    def shutdown(self) -> None:
        """Shutdown the application and clean up resources."""
        # Unregister hotkey
        self.hotkey_handler.unregister()
        
        # Stop any ongoing recording
        if self.audio_recorder.is_recording():
            self.audio_recorder.stop_recording()

