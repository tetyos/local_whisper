"""Transcriber module using faster-whisper for speech-to-text."""

import os
import numpy as np
from pathlib import Path
from typing import Optional
from faster_whisper import WhisperModel


def get_model_directory() -> Path:
    """Get the directory for storing Whisper models."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    model_dir = Path(appdata) / 'luca-whisper' / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


class Transcriber:
    """Transcribes audio using the Whisper model."""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Size of the Whisper model ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to use ('cpu', 'cuda', or 'auto')
        """
        self.model_size = model_size
        self.device = device
        self.model: Optional[WhisperModel] = None
        self._model_dir = get_model_directory()
    
    def load_model(self, on_progress: Optional[callable] = None) -> None:
        """
        Load the Whisper model.
        
        Args:
            on_progress: Optional callback for download progress
        """
        # Determine compute type based on device
        if self.device == "auto":
            # Try CUDA first, fall back to CPU
            try:
                import torch
                if torch.cuda.is_available():
                    compute_type = "float16"
                    device = "cuda"
                else:
                    compute_type = "int8"
                    device = "cpu"
            except ImportError:
                compute_type = "int8"
                device = "cpu"
        elif self.device == "cuda":
            compute_type = "float16"
            device = "cuda"
        else:
            compute_type = "int8"
            device = "cpu"
        
        self.model = WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(self._model_dir)
        )
    
    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy array (float32, 16kHz)
            language: Optional language code (e.g., 'en', 'de'). Auto-detect if None.
        
        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if len(audio) == 0:
            return ""
        
        # Transcribe the audio
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,  # Filter out silence
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )
        
        # Combine all segments into a single string
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
        
        return " ".join(text_parts)
    
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self.model is not None
    
    @staticmethod
    def get_available_models() -> list[dict]:
        """Get list of available Whisper models with their sizes."""
        return [
            {"name": "tiny", "size": "~75 MB", "description": "Fastest, basic accuracy"},
            {"name": "base", "size": "~150 MB", "description": "Good balance"},
            {"name": "small", "size": "~500 MB", "description": "Better accuracy"},
            {"name": "medium", "size": "~1.5 GB", "description": "High accuracy"},
            {"name": "large", "size": "~3 GB", "description": "Best accuracy"},
        ]

