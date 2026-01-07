"""Audio recording module for capturing microphone input."""

import numpy as np
import sounddevice as sd
from typing import Optional
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal


class AudioRecorder(QObject):
    """Records audio from the default microphone."""
    
    # Signal emitted with audio level (0.0-1.0) during recording
    audio_level_changed = pyqtSignal(float)
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Sample rate for recording (16000 Hz is optimal for Whisper)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._last_level_emit_time: float = 0.0
        self._level_emit_interval: float = 0.05  # Emit every 50ms
    
    def _calculate_rms(self, audio_chunk: np.ndarray) -> float:
        """
        Calculate the RMS (Root Mean Square) of an audio chunk.
        
        Returns a value between 0.0 and 1.0.
        """
        if len(audio_chunk) == 0:
            return 0.0
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Normalize to 0.0-1.0 range
        # Audio is float32 in range [-1.0, 1.0], so max RMS is 1.0
        # Apply some scaling for better visualization (speech is typically quieter)
        # Multiply by ~3-4 to make normal speech levels more visible
        normalized = min(1.0, rms * 3.5)
        
        return float(normalized)
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                        time_info: dict, status: sd.CallbackFlags) -> None:
        """Callback function for audio stream."""
        if status:
            print(f"Audio status: {status}")
        
        with self._lock:
            if self.recording:
                self.audio_data.append(indata.copy())
        
        # Emit audio level periodically
        current_time = time.time()
        if current_time - self._last_level_emit_time >= self._level_emit_interval:
            self._last_level_emit_time = current_time
            level = self._calculate_rms(indata)
            self.audio_level_changed.emit(level)
    
    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        with self._lock:
            self.audio_data = []
            self.recording = True
        
        self._last_level_emit_time = time.time()
        
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            callback=self._audio_callback
        )
        self._stream.start()
    
    def stop_recording(self) -> np.ndarray:
        """
        Stop recording and return the recorded audio.
        
        Returns:
            numpy array containing the recorded audio data
        """
        with self._lock:
            self.recording = False
        
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        with self._lock:
            if self.audio_data:
                # Concatenate all recorded chunks
                audio = np.concatenate(self.audio_data, axis=0)
                # Flatten to 1D array
                audio = audio.flatten()
                return audio
            else:
                return np.array([], dtype=np.float32)
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self.recording
    
    @staticmethod
    def get_available_devices() -> list[dict]:
        """Get list of available audio input devices."""
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return input_devices
