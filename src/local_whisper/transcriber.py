"""Transcriber module using faster-whisper for speech-to-text."""

import os
import numpy as np
import threading
import time
from pathlib import Path
from typing import Optional, Callable
from faster_whisper import WhisperModel
from huggingface_hub import hf_hub_download, HfApi


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


def _get_incomplete_files_size(cache_dir: Path) -> int:
    """
    Get total size of incomplete files being downloaded.
    
    HuggingFace Hub stores incomplete downloads as .incomplete files.
    We search recursively for these files in the cache directory.
    """
    total = 0
    seen_paths = set()
    
    try:
        # Search for .incomplete files recursively
        # These are the temporary files created during download
        for incomplete_file in cache_dir.rglob("*.incomplete"):
            try:
                # Use resolved path to avoid counting same file twice
                file_path = incomplete_file.resolve()
                if file_path in seen_paths:
                    continue
                seen_paths.add(file_path)
                
                # Get file size
                size = incomplete_file.stat().st_size
                total += size
            except (OSError, FileNotFoundError):
                # File might have been completed or deleted between check and stat
                pass
    except Exception:
        # If there's any error searching, return 0
        pass
    
    return total


def download_model(
    model_name: str, 
    on_progress: Optional[Callable[[float, str], None]] = None
) -> None:
    """
    Download a model from HuggingFace Hub with real-time progress tracking.
    
    Monitors download progress by watching .incomplete files in the cache.
    
    Args:
        model_name: Name of the model to download
        on_progress: Optional callback(progress_percent, status_message)
    """
    repo_name = MODEL_REPO_MAP.get(model_name, model_name)
    model_dir = get_model_directory()
    model_cache_dir = get_model_path(model_name)  # Specific model cache directory
    
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
        
        # Track completed downloads with thread-safe locking
        completed_bytes = 0
        completed_lock = threading.Lock()
        stop_monitoring = threading.Event()
        current_file_info = {'name': '', 'size': 0}
        current_file_lock = threading.Lock()
        
        def progress_monitor():
            """Background thread to monitor download progress."""
            last_reported_percent = -1
            while not stop_monitoring.is_set():
                try:
                    # Get size of incomplete files - check both root cache and model-specific cache
                    incomplete_size = _get_incomplete_files_size(model_dir)
                    # Also check the model-specific cache directory
                    if model_cache_dir.exists():
                        incomplete_size += _get_incomplete_files_size(model_cache_dir)
                    
                    # Get completed bytes safely
                    with completed_lock:
                        completed = completed_bytes
                    
                    # Total progress = completed files + current download progress
                    current_progress = completed + incomplete_size
                    
                    # Calculate percentage
                    if total_bytes > 0:
                        percent = (current_progress / total_bytes) * 100
                        percent = min(99.9, max(0, percent))
                        
                        # Update if progress changed by at least 0.1% to avoid too frequent updates
                        if abs(percent - last_reported_percent) >= 0.1:
                            last_reported_percent = percent
                            
                            if on_progress:
                                with current_file_lock:
                                    display_name = current_file_info['name'] or "files"
                                
                                downloaded_str = _format_bytes(current_progress)
                                total_str = _format_bytes(total_bytes)
                                on_progress(percent, f"Downloading {display_name} ({downloaded_str}/{total_str})")
                    
                    time.sleep(0.1)  # Check every 100ms for smoother updates
                except Exception:
                    time.sleep(0.5)
        
        # Start progress monitoring thread
        monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
        monitor_thread.start()
        
        try:
            # Download each file
            for file_info in files_to_download:
                filename = file_info['filename']
                file_size = file_info['size']
                
                # Clean filename for display
                display_name = filename.split('/')[-1] if '/' in filename else filename
                with current_file_lock:
                    current_file_info['name'] = display_name
                    current_file_info['size'] = file_size
                
                # Download the file (this blocks until download completes)
                hf_hub_download(
                    repo_id=repo_name,
                    filename=filename,
                    cache_dir=str(model_dir),
                    local_files_only=False,
                )
                
                # Update completed bytes after file finishes
                with completed_lock:
                    completed_bytes += file_size
                
                # Force a progress update after file completes
                if on_progress and total_bytes > 0:
                    with completed_lock:
                        completed = completed_bytes
                    percent = (completed / total_bytes) * 100
                    percent = min(99.9, max(0, percent))
                    downloaded_str = _format_bytes(completed)
                    total_str = _format_bytes(total_bytes)
                    on_progress(percent, f"Downloaded {display_name} ({downloaded_str}/{total_str})")
                
        finally:
            # Stop monitoring thread
            stop_monitoring.set()
            monitor_thread.join(timeout=2.0)
        
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
