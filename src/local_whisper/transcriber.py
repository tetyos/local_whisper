"""Transcriber module using faster-whisper for speech-to-text."""

import os
import numpy as np
import threading
from pathlib import Path
from typing import Optional, Callable
from faster_whisper import WhisperModel
from huggingface_hub import hf_hub_download, HfApi
from tqdm import tqdm


# Mapping of model names to HuggingFace repo names
MODEL_REPO_MAP = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}


def get_model_directory() -> Path:
    """Get the directory for storing Whisper models."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    model_dir = Path(appdata) / 'local-whisper' / 'models'
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


def _format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


class _ProgressTracker(tqdm):
    """
    Custom tqdm class that captures progress updates from HuggingFace downloads.
    
    This hooks into HuggingFace Hub's internal tqdm usage to get accurate
    byte-level progress instead of relying on file system checks.
    """
    
    # Class-level state shared across all instances during a download session
    _callback = None
    _total_bytes = 0
    _completed_bytes = 0
    _current_file = ""
    _current_file_size = 0
    _current_file_started = False
    _lock = threading.Lock()
    
    @classmethod
    def reset_state(cls, callback, total_bytes):
        """Reset tracking state for a new download session."""
        with cls._lock:
            cls._callback = callback
            cls._total_bytes = total_bytes
            cls._completed_bytes = 0
            cls._current_file = ""
            cls._current_file_size = 0
            cls._current_file_started = False
    
    @classmethod
    def set_current_file(cls, filename, size):
        """Set the current file being downloaded."""
        with cls._lock:
            # If previous file didn't trigger any download (was cached),
            # add its size to completed bytes
            if cls._current_file and not cls._current_file_started:
                cls._completed_bytes += cls._current_file_size
                cls._report_progress()
            
            cls._current_file = filename
            cls._current_file_size = size
            cls._current_file_started = False
    
    @classmethod
    def finalize(cls):
        """Call after all downloads to handle the last cached file if any."""
        with cls._lock:
            # Handle final file if it was cached (no download triggered)
            if cls._current_file and not cls._current_file_started:
                cls._completed_bytes += cls._current_file_size
            cls._current_file = ""
            cls._current_file_size = 0
            cls._current_file_started = False
    
    @classmethod
    def _report_progress(cls):
        """Report current progress to callback."""
        if cls._callback and cls._total_bytes > 0:
            percent = (cls._completed_bytes / cls._total_bytes) * 100
            percent = min(99.9, max(0, percent))
            downloaded_str = _format_bytes(cls._completed_bytes)
            total_str = _format_bytes(cls._total_bytes)
            cls._callback(percent, f"Downloading {cls._current_file} ({downloaded_str}/{total_str})")
    
    def __init__(self, *args, **kwargs):
        # Store the file size for this specific download
        self._file_total = kwargs.get('total', 0) or 0
        self._file_progress = 0
        self._closed = False  # Guard against double close() calls
        # Mark that download has started for current file
        with _ProgressTracker._lock:
            _ProgressTracker._current_file_started = True
        
        # Remove kwargs that tqdm doesn't recognize (HuggingFace adds 'name')
        kwargs.pop('name', None)
        super().__init__(*args, **kwargs)
    
    def update(self, n=1):
        """Called by HuggingFace when bytes are downloaded."""
        super().update(n)
        
        with _ProgressTracker._lock:
            # Track progress for this file
            self._file_progress += n
            
            # Calculate overall progress
            overall_progress = _ProgressTracker._completed_bytes + self._file_progress
            
            if _ProgressTracker._callback and _ProgressTracker._total_bytes > 0:
                percent = (overall_progress / _ProgressTracker._total_bytes) * 100
                percent = min(99.9, max(0, percent))
                downloaded_str = _format_bytes(overall_progress)
                total_str = _format_bytes(_ProgressTracker._total_bytes)
                _ProgressTracker._callback(
                    percent, 
                    f"Downloading {_ProgressTracker._current_file} ({downloaded_str}/{total_str})"
                )
    
    def close(self):
        """Called when download completes. May be called multiple times by tqdm."""
        super().close()
        with _ProgressTracker._lock:
            # Guard against double close() calls (tqdm may call close() multiple times)
            if self._closed:
                return
            self._closed = True
            
            # Use file_progress if file_total is 0 (HF doesn't always provide Content-Length)
            bytes_to_add = self._file_total if self._file_total > 0 else self._file_progress
            _ProgressTracker._completed_bytes += bytes_to_add


def download_model(
    model_name: str, 
    on_progress: Optional[Callable[[float, str], None]] = None
) -> None:
    """
    Download a model from HuggingFace Hub with real-time progress tracking.
    
    Uses a custom tqdm class to capture actual download progress from
    HuggingFace Hub's internal progress reporting.
    
    Args:
        model_name: Name of the model to download
        on_progress: Optional callback(progress_percent, status_message)
    """
    repo_name = MODEL_REPO_MAP.get(model_name, model_name)
    model_dir = get_model_directory()
    
    if on_progress:
        on_progress(0, f"Starting download of {model_name}...")
    
    try:
        # Get list of files and their sizes
        api = HfApi()
        repo_info = api.repo_info(repo_id=repo_name, repo_type="model", files_metadata=True)
        
        # Calculate total size and build file list with sizes
        files_to_download = []
        total_bytes = 0
        
        for sibling in repo_info.siblings:
            file_size = sibling.size if sibling.size else 0
            files_to_download.append({
                'filename': sibling.rfilename,
                'size': file_size
            })
            total_bytes += file_size
        
        if on_progress:
            total_str = _format_bytes(total_bytes)
            on_progress(1, f"Found {len(files_to_download)} files ({total_str})")
        
        # Sort files by size - download smaller files first for quicker initial progress
        files_to_download.sort(key=lambda x: x['size'])
        
        # Initialize progress tracker
        _ProgressTracker.reset_state(on_progress, total_bytes)
        
        # Download each file
        for file_info in files_to_download:
            filename = file_info['filename']
            file_size = file_info['size']
            
            # Clean filename for display
            display_name = filename.split('/')[-1] if '/' in filename else filename
            _ProgressTracker.set_current_file(display_name, file_size)
            
            # Download the file using our custom tqdm class for progress tracking
            hf_hub_download(
                repo_id=repo_name,
                filename=filename,
                cache_dir=str(model_dir),
                local_files_only=False,
                tqdm_class=_ProgressTracker,
            )
        
        # Finalize progress tracking (handles cached files)
        _ProgressTracker.finalize()
        
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
        {"name": "tiny", "display_name": "OpenAI Whisper Tiny", "size": "~75 MB", "description": "Fastest, basic accuracy"},
        {"name": "base", "display_name": "OpenAI Whisper Base", "size": "~150 MB", "description": "Good balance"},
        {"name": "small", "display_name": "OpenAI Whisper Small", "size": "~500 MB", "description": "Better accuracy"},
        {"name": "medium", "display_name": "OpenAI Whisper Medium", "size": "~1.5 GB", "description": "High accuracy"},
        {"name": "large-v3", "display_name": "OpenAI Whisper Large V3", "size": "~3 GB", "description": "Best accuracy"},
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
        
        Download and loading are separate phases:
        - Download phase: 0-100% for downloading files
        - Loading phase: Separate "Loading model into memory..." message
        
        Args:
            on_progress: Optional callback for download/load progress
        """
        # Check if model needs to be downloaded
        if not is_model_downloaded(self.model_size):
            download_model(self.model_size, on_progress)
        
        # Loading phase - separate from download
        # Use a special progress value or message to indicate loading
        if on_progress:
            on_progress(0, "Loading model into memory...")
        
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
    
    def transcribe(
        self, 
        audio: np.ndarray, 
        language: Optional[str] = None,
        on_progress: Optional[Callable[[float, float], None]] = None
    ) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio: Audio data as numpy array (float32, 16kHz)
            language: Optional language code (e.g., 'en', 'de'). Auto-detect if None.
            on_progress: Optional callback(progress_percent, audio_duration) called during transcription.
                         progress_percent is 0-100 based on processed audio time.
        
        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if len(audio) == 0:
            return ""
        
        # Calculate audio duration for progress tracking
        audio_duration = len(audio) / 16000.0  # Assuming 16kHz sample rate
        
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
        
        # Combine all segments into a single string, tracking progress
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
            
            # Report progress based on segment end time
            if on_progress and audio_duration > 0:
                progress = min(100.0, (segment.end / audio_duration) * 100.0)
                on_progress(progress, audio_duration)
        
        # Final progress update
        if on_progress:
            on_progress(100.0, audio_duration)
        
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
