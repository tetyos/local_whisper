"""Audio recording module for capturing microphone input."""

import numpy as np
import sounddevice as sd
from typing import Optional
import threading


class AudioRecorder:
    """Records audio from the default microphone."""
    
    def __init__(self, sample_rate: int = 16000):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Sample rate for recording (16000 Hz is optimal for Whisper)
        """
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
    
    def _audio_callback(self, indata: np.ndarray, frames: int, 
                        time_info: dict, status: sd.CallbackFlags) -> None:
        """Callback function for audio stream."""
        if status:
            print(f"Audio status: {status}")
        
        with self._lock:
            if self.recording:
                self.audio_data.append(indata.copy())
    
    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        with self._lock:
            self.audio_data = []
            self.recording = True
        
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

