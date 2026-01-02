"""Transcriber module using faster-whisper for speech-to-text."""

import os
import numpy as np
from pathlib import Path
from typing import Optional, Callable
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download, HfFileSystem


# Mapping of model names to HuggingFace repo names
MODEL_REPO_MAP = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
}


def get_model_directory() -> Path:
    """Get the directory for storing Whisper models."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    model_dir = Path(appdata) / 'luca-whisper' / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


def get_model_path(model_name: str) -> Path:
    """Get the path where a specific model would be stored."""
    repo_name = MODEL_REPO_MAP.get(model_name, model_name)
    # HuggingFace stores models in models--org--name format
    cache_name = f"models--{repo_name.replace('/', '--')}"
    return get_model_directory() / cache_name


def is_model_downloaded(model_name: str) -> bool:
    """
    Check if a model is already downloaded locally.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if the model is downloaded and ready to use
    """
    model_path = get_model_path(model_name)
    
    if not model_path.exists():
        return False
    
    # Check for snapshots directory which contains the actual model files
    snapshots_dir = model_path / "snapshots"
    if not snapshots_dir.exists():
        return False
    
    # Check if there's at least one snapshot with model files
    for snapshot in snapshots_dir.iterdir():
        if snapshot.is_dir():
            # Check for essential model file
            model_bin = snapshot / "model.bin"
            if model_bin.exists():
                return True
    
    return False


def download_model(
    model_name: str, 
    on_progress: Optional[Callable[[float, str], None]] = None
) -> None:
    """
    Download a model from HuggingFace Hub.
    
    Args:
        model_name: Name of the model to download
        on_progress: Optional callback(progress_percent, status_message)
    """
    repo_name = MODEL_REPO_MAP.get(model_name, model_name)
    model_dir = get_model_directory()
    
    if on_progress:
        on_progress(0, f"Starting download of {model_name}...")
    
    try:
        # Download the model using huggingface_hub
        snapshot_download(
            repo_id=repo_name,
            local_dir=None,  # Use default cache structure
            cache_dir=str(model_dir),
            local_files_only=False,
        )
        
        if on_progress:
            on_progress(100, f"Download complete: {model_name}")
            
    except Exception as e:
        if on_progress:
            on_progress(-1, f"Download failed: {str(e)}")
        raise


class Transcriber:
    """Transcribes audio using the Whisper model."""
    
    # Available models with metadata
    AVAILABLE_MODELS = [
        {"name": "tiny", "size": "~75 MB", "description": "Fastest, basic accuracy"},
        {"name": "base", "size": "~150 MB", "description": "Good balance"},
        {"name": "small", "size": "~500 MB", "description": "Better accuracy"},
        {"name": "medium", "size": "~1.5 GB", "description": "High accuracy"},
        {"name": "large", "size": "~3 GB", "description": "Best accuracy (v1)"},
        {"name": "large-v2", "size": "~3 GB", "description": "Improved large model"},
        {"name": "large-v3", "size": "~3 GB", "description": "Latest large model"},
    ]
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Size of the Whisper model
            device: Device to use ('cpu', 'cuda', or 'auto')
        """
        self.model_size = model_size
        self.device = device
        self.model: Optional[WhisperModel] = None
        self._model_dir = get_model_directory()
    
    def set_model_size(self, model_size: str) -> None:
        """
        Set the model size. Unloads current model if different.
        
        Args:
            model_size: New model size to use
        """
        if model_size != self.model_size:
            self.model = None  # Unload current model
            self.model_size = model_size
    
    def load_model(self, on_progress: Optional[Callable[[float, str], None]] = None) -> None:
        """
        Load the Whisper model. Downloads if not available locally.
        
        Args:
            on_progress: Optional callback for download/load progress
        """
        # Check if model needs to be downloaded
        if not is_model_downloaded(self.model_size):
            download_model(self.model_size, on_progress)
        
        if on_progress:
            on_progress(50, "Loading model into memory...")
        
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
        
        if on_progress:
            on_progress(100, "Model loaded successfully")
    
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
        return Transcriber.AVAILABLE_MODELS.copy()
    
    @staticmethod
    def is_model_downloaded(model_name: str) -> bool:
        """Check if a specific model is downloaded locally."""
        return is_model_downloaded(model_name)
