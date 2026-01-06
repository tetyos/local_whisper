"""Main application class that coordinates all components."""

from enum import Enum, auto
from typing import Optional
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from .audio_recorder import AudioRecorder
from .transcriber import Transcriber, is_model_downloaded, download_model
from .hotkey_handler import HotkeyHandler
from .text_output import TextOutput
from .settings import (
    get_selected_model, set_selected_model,
    record_transcription_time, get_estimated_transcription_time
)


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
    download_progress = pyqtSignal(str, float, str)  # model_name, progress (0-100), message
    download_complete = pyqtSignal(str)  # model_name - emitted when download finishes
    model_ready = pyqtSignal(str)  # model_name - emitted when model is loaded into memory
    transcription_progress = pyqtSignal(float, float, float)  # progress (0-100), elapsed_seconds, eta_seconds
    
    # Internal signals for thread-safe operations
    _update_progress = pyqtSignal(float, float)
    _start_progress_timer = pyqtSignal(int)
    _stop_progress_timer = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Load selected model from settings
        self._selected_model = get_selected_model()
        
        # Verify model exists, fallback if not
        if self._selected_model and not is_model_downloaded(self._selected_model):
            # Try to find another downloaded model
            found_fallback = False
            for model_info in Transcriber.get_available_models():
                name = model_info['name']
                if is_model_downloaded(name):
                    self._selected_model = name
                    set_selected_model(name)
                    found_fallback = True
                    break
            
            if not found_fallback:
                self._selected_model = ""
        
        # Initialize components
        self.audio_recorder = AudioRecorder(sample_rate=16000)
        self.transcriber = Transcriber(model_size=self._selected_model, device="auto")
        self.hotkey_handler = HotkeyHandler(hotkey="ctrl+space")
        self.text_output = TextOutput(typing_interval=0.005)
        
        # State
        self._state = AppState.LOADING
        self._lock = threading.Lock()
        self._hotkey_registered = False
        self._downloading_model: str = ""  # Track which model is being downloaded
        
        # Transcription progress tracking
        self._transcription_start_time: float = 0.0
        self._transcription_estimated_time: float = 0.0
        self._transcription_progress: float = 0.0
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_elapsed_time)
        
        # Connect internal signals for thread-safe updates
        self._update_progress.connect(self._on_progress_from_thread)
        self._start_progress_timer.connect(self._on_start_progress_timer)
        self._stop_progress_timer.connect(self._on_stop_progress_timer)
    
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
    
    @property
    def is_downloading(self) -> bool:
        """Check if a download is in progress."""
        return self._downloading_model != ""
    
    def _register_hotkey(self) -> None:
        """Register the hotkey if not already registered."""
        if not self._hotkey_registered:
            self.hotkey_handler.register(self._on_hotkey_pressed)
            self._hotkey_registered = True
    
    def _update_elapsed_time(self) -> None:
        """Timer callback to update elapsed time during transcription."""
        if self._transcription_start_time > 0:
            elapsed = time.time() - self._transcription_start_time
            
            # Calculate remaining time and progress
            if self._transcription_progress > 0:
                # We have real progress from segments
                total_estimated = elapsed / (self._transcription_progress / 100.0)
                remaining = max(0, total_estimated - elapsed)
                current_progress = self._transcription_progress
            else:
                # No segments finished yet (or single segment)
                # Estimate based on expected duration
                # Allow progress to move up to 95% based on time
                if self._transcription_estimated_time > 0:
                    time_progress = (elapsed / self._transcription_estimated_time) * 100.0
                    current_progress = min(95.0, time_progress)
                    remaining = max(0, self._transcription_estimated_time - elapsed)
                else:
                    current_progress = 0.0
                    remaining = 0.0
            
            # If we've exceeded estimate but still running, show indeterminate/finishing state
            # by keeping remaining at 0 (handled by max(0, ...))
            
            self.transcription_progress.emit(current_progress, elapsed, remaining)
    
    def _on_progress_from_thread(self, progress: float, audio_duration: float) -> None:
        """Handle progress updates from background thread (thread-safe via signal)."""
        self._transcription_progress = progress
    
    def _on_start_progress_timer(self, interval: int) -> None:
        """Start the progress timer (called from main thread via signal)."""
        self._transcription_start_time = time.time()
        self._progress_timer.start(interval)
    
    def _on_stop_progress_timer(self) -> None:
        """Stop the progress timer (called from main thread via signal)."""
        self._progress_timer.stop()
        self._transcription_start_time = 0.0
    
    def initialize(self) -> None:
        """Initialize the application (load model if available, register hotkey)."""
        self.state = AppState.LOADING
        
        # Register hotkey early so it's available
        self._register_hotkey()
        
        # Check if the selected model exists and is downloaded
        if self._selected_model and is_model_downloaded(self._selected_model):
            self.state_changed.emit(AppState.LOADING, f"Loading {self._selected_model} model...")
            self._load_model_async()
        else:
            # No model selected or model not downloaded - wait for user action
            self._selected_model = ""
            self.state = AppState.NO_MODEL
            self.state_changed.emit(
                AppState.NO_MODEL, 
                "No model downloaded. Please select and download a model first."
            )
    
    def _load_model_async(self) -> None:
        """Load the model in a background thread."""
        def load_model():
            try:
                # Model is already downloaded, just load it
                self.transcriber.load_model()
                
                self.state = AppState.IDLE
                self.state_changed.emit(AppState.IDLE, "Ready")
                self.model_ready.emit(self._selected_model)
                
            except Exception as e:
                self.state = AppState.ERROR
                self.error_occurred.emit(f"Failed to load model: {str(e)}")
        
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()
    
    def select_model(self, model_name: str) -> None:
        """
        Select and load an already-downloaded model.
        
        This method is for switching to a model that is already downloaded.
        It will load the model into memory.
        
        Args:
            model_name: Name of the model to select
        """
        if model_name == self._selected_model and self.transcriber.is_loaded():
            # Same model, already loaded
            return
        
        # Don't allow model change while recording or transcribing
        current_state = self.state
        if current_state in (AppState.RECORDING, AppState.TRANSCRIBING, AppState.TYPING, AppState.DOWNLOADING):
            self.error_occurred.emit("Cannot change model while busy. Please wait.")
            return
        
        # Verify model is downloaded
        if not is_model_downloaded(model_name):
            self.error_occurred.emit(f"Model '{model_name}' is not downloaded. Please download it first.")
            return
        
        # Update selected model
        self._selected_model = model_name
        set_selected_model(model_name)
        self.transcriber.set_model_size(model_name)
        
        # Load the model
        self.state = AppState.LOADING
        self.state_changed.emit(AppState.LOADING, f"Loading {model_name} into memory...")
        self._load_model_async()
    
    def start_download(self, model_name: str) -> None:
        """
        Start downloading a model.
        
        This method only downloads the model, it does not select or load it.
        The download_complete signal will be emitted when done.
        
        Args:
            model_name: Name of the model to download
        """
        # Don't allow multiple simultaneous downloads
        if self.is_downloading:
            self.error_occurred.emit("A download is already in progress. Please wait.")
            return
        
        # Check if already downloaded
        if is_model_downloaded(model_name):
            self.error_occurred.emit(f"Model '{model_name}' is already downloaded.")
            return
        
        self._downloading_model = model_name
        self.state = AppState.DOWNLOADING
        self.state_changed.emit(AppState.DOWNLOADING, f"Downloading {model_name}...")
        
        def do_download():
            try:
                def on_progress(progress: float, message: str):
                    """Handle download progress updates."""
                    self.download_progress.emit(model_name, progress, message)
                
                # Download the model
                download_model(model_name, on_progress=on_progress)
                
                # Download complete
                self._downloading_model = ""
                self.download_complete.emit(model_name)
                
                # Return to previous state
                if self.transcriber.is_loaded():
                    self.state = AppState.IDLE
                    self.state_changed.emit(AppState.IDLE, "Ready")
                else:
                    self.state = AppState.NO_MODEL
                    self.state_changed.emit(AppState.NO_MODEL, "Select a model to use")
                
            except Exception as e:
                self._downloading_model = ""
                self.state = AppState.ERROR
                self.error_occurred.emit(f"Download failed: {str(e)}")
        
        thread = threading.Thread(target=do_download, daemon=True)
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
            
            # Calculate audio duration and get estimated time
            audio_duration = len(audio_data) / 16000.0  # 16kHz sample rate
            estimated_time = get_estimated_transcription_time(self._selected_model, audio_duration)
            
            self.state = AppState.TRANSCRIBING
            self.state_changed.emit(AppState.TRANSCRIBING, "Transcribing...")
            
            # Initialize progress tracking
            self._transcription_estimated_time = estimated_time
            self._transcription_progress = 0.0
            
            # Emit initial progress with ETA
            self.transcription_progress.emit(0.0, 0.0, estimated_time)
            
            # Start timer to update elapsed time every 100ms (thread-safe via signal)
            # We use 100ms for smoother UI updates
            self._start_progress_timer.emit(100)
            
            # Transcribe in background thread
            def transcribe_and_type():
                def on_progress(progress: float, audio_dur: float):
                    """Handle transcription progress updates (from background thread)."""
                    # Use signal to update progress thread-safely
                    self._update_progress.emit(progress, audio_dur)
                
                try:
                    text = self.transcriber.transcribe(audio_data, on_progress=on_progress)
                    
                    # Record actual transcription time for future estimates
                    elapsed_time = time.time() - self._transcription_start_time
                    record_transcription_time(self._selected_model, audio_duration, elapsed_time)
                    
                    # Stop the progress timer (thread-safe via signal)
                    self._stop_progress_timer.emit()
                    
                    if text.strip():
                        self.state = AppState.TYPING
                        self.state_changed.emit(AppState.TYPING, "Typing...")
                        
                        # Type the text
                        self.text_output.type_text(text.strip())
                    
                    self.state = AppState.IDLE
                    self.state_changed.emit(AppState.IDLE, "Ready")
                    
                except Exception as e:
                    self._stop_progress_timer.emit()
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
