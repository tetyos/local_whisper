"""Tests for the transcriber module."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np

from local_whisper.transcriber import (
    get_model_directory,
    get_model_path,
    is_model_downloaded,
    _format_bytes,
    download_model,
    Transcriber,
    MODEL_REPO_MAP,
)


class TestFormatBytes:
    """Tests for the _format_bytes utility function."""
    
    def test_format_bytes_bytes(self):
        """Test formatting bytes (< 1KB)."""
        assert _format_bytes(0) == "0 B"
        assert _format_bytes(1) == "1 B"
        assert _format_bytes(512) == "512 B"
        assert _format_bytes(1023) == "1023 B"
    
    def test_format_bytes_kilobytes(self):
        """Test formatting kilobytes (1KB - 1MB)."""
        assert _format_bytes(1024) == "1.0 KB"
        assert _format_bytes(1536) == "1.5 KB"
        assert _format_bytes(10240) == "10.0 KB"
        assert _format_bytes(1024 * 1024 - 1) == "1024.0 KB"
    
    def test_format_bytes_megabytes(self):
        """Test formatting megabytes (1MB - 1GB)."""
        assert _format_bytes(1024 * 1024) == "1.0 MB"
        assert _format_bytes(1024 * 1024 * 1.5) == "1.5 MB"
        assert _format_bytes(1024 * 1024 * 100) == "100.0 MB"
        assert _format_bytes(1024 * 1024 * 1024 - 1) == "1024.0 MB"
    
    def test_format_bytes_gigabytes(self):
        """Test formatting gigabytes (>= 1GB)."""
        assert _format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert _format_bytes(int(1024 * 1024 * 1024 * 1.5)) == "1.50 GB"
        assert _format_bytes(1024 * 1024 * 1024 * 3) == "3.00 GB"


class TestModelDirectory:
    """Tests for model directory functions."""
    
    def test_get_model_directory_creates_dir(self, temp_model_dir: Path, monkeypatch):
        """Test that get_model_directory creates the directory."""
        import shutil
        if temp_model_dir.exists():
            shutil.rmtree(temp_model_dir)
        
        result = get_model_directory()
        
        assert result.exists()
        assert result.is_dir()
        assert result.name == "models"
    
    def test_get_model_path_uses_repo_map(self, temp_model_dir: Path):
        """Test that get_model_path uses the MODEL_REPO_MAP."""
        result = get_model_path("tiny")
        
        expected_cache_name = "models--Systran--faster-whisper-tiny"
        assert result.name == expected_cache_name
    
    def test_get_model_path_handles_unknown_model(self, temp_model_dir: Path):
        """Test get_model_path with unknown model name."""
        result = get_model_path("custom/model-name")
        
        expected_cache_name = "models--custom--model-name"
        assert result.name == expected_cache_name


class TestIsModelDownloaded:
    """Tests for checking if model is downloaded."""
    
    def test_returns_false_when_path_not_exists(self, temp_model_dir: Path):
        """Test returns False when model path doesn't exist."""
        result = is_model_downloaded("nonexistent-model")
        
        assert result is False
    
    def test_returns_false_when_no_snapshots(self, temp_model_dir: Path):
        """Test returns False when no snapshots directory."""
        model_path = get_model_path("tiny")
        model_path.mkdir(parents=True, exist_ok=True)
        
        result = is_model_downloaded("tiny")
        
        assert result is False
    
    def test_returns_false_when_no_model_bin(self, temp_model_dir: Path):
        """Test returns False when no model.bin file."""
        model_path = get_model_path("tiny")
        snapshots_dir = model_path / "snapshots" / "abc123"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        result = is_model_downloaded("tiny")
        
        assert result is False
    
    def test_returns_true_when_model_exists(self, fake_downloaded_model: str):
        """Test returns True when model.bin exists."""
        result = is_model_downloaded(fake_downloaded_model)
        
        assert result is True


class TestModelRepoMap:
    """Tests for MODEL_REPO_MAP constant."""
    
    def test_contains_all_standard_models(self):
        """Test that MODEL_REPO_MAP contains all standard models."""
        expected_models = ["tiny", "base", "small", "medium", "large-v3"]
        
        for model in expected_models:
            assert model in MODEL_REPO_MAP
    
    def test_repo_names_are_systran(self):
        """Test that all repos are from Systran."""
        for model, repo in MODEL_REPO_MAP.items():
            assert repo.startswith("Systran/faster-whisper-")


class TestTranscriberClass:
    """Tests for the Transcriber class."""
    
    def test_init_default_values(self):
        """Test Transcriber initialization with defaults."""
        transcriber = Transcriber()
        
        assert transcriber.model_size == "base"
        assert transcriber.device == "auto"
        assert transcriber.model is None
    
    def test_init_custom_values(self):
        """Test Transcriber initialization with custom values."""
        transcriber = Transcriber(model_size="small", device="cpu")
        
        assert transcriber.model_size == "small"
        assert transcriber.device == "cpu"
    
    def test_is_loaded_returns_false_initially(self):
        """Test that is_loaded returns False before loading."""
        transcriber = Transcriber()
        
        assert transcriber.is_loaded() is False
    
    def test_set_model_size_changes_size(self):
        """Test that set_model_size changes the model size."""
        transcriber = Transcriber(model_size="base")
        transcriber.set_model_size("medium")
        
        assert transcriber.model_size == "medium"
    
    def test_set_model_size_unloads_model(self, mock_whisper_model):
        """Test that set_model_size unloads current model."""
        transcriber = Transcriber(model_size="base")
        transcriber.model = mock_whisper_model  # Simulate loaded model
        
        transcriber.set_model_size("medium")
        
        assert transcriber.model is None
    
    def test_set_model_size_same_size_no_unload(self, mock_whisper_model):
        """Test that set_model_size with same size doesn't unload."""
        transcriber = Transcriber(model_size="base")
        transcriber.model = mock_whisper_model
        
        transcriber.set_model_size("base")
        
        assert transcriber.model is mock_whisper_model
    
    def test_get_available_models_returns_list(self):
        """Test that get_available_models returns a list of dicts."""
        result = Transcriber.get_available_models()
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(m, dict) for m in result)
    
    def test_get_available_models_has_required_keys(self):
        """Test that each model has required keys."""
        result = Transcriber.get_available_models()
        
        required_keys = ["name", "display_name", "size", "description"]
        for model in result:
            for key in required_keys:
                assert key in model
    
    def test_get_available_models_returns_copy(self):
        """Test that get_available_models returns a copy."""
        result1 = Transcriber.get_available_models()
        result2 = Transcriber.get_available_models()
        
        result1.append({"fake": "model"})
        
        assert len(result1) != len(result2)
    
    def test_is_model_downloaded_static_method(self, fake_downloaded_model: str):
        """Test the static is_model_downloaded method."""
        assert Transcriber.is_model_downloaded(fake_downloaded_model) is True
        assert Transcriber.is_model_downloaded("nonexistent") is False
    
    def test_transcribe_raises_when_model_not_loaded(self):
        """Test that transcribe raises error when model not loaded."""
        transcriber = Transcriber()
        audio = np.zeros(16000, dtype=np.float32)
        
        with pytest.raises(RuntimeError, match="Model not loaded"):
            transcriber.transcribe(audio)
    
    def test_transcribe_returns_empty_for_empty_audio(self, mock_whisper_model):
        """Test that transcribe returns empty string for empty audio."""
        transcriber = Transcriber()
        transcriber.model = mock_whisper_model
        
        result = transcriber.transcribe(np.array([], dtype=np.float32))
        
        assert result == ""
    
    def test_transcribe_returns_text(self, mock_whisper_model):
        """Test that transcribe returns transcribed text."""
        transcriber = Transcriber()
        transcriber.model = mock_whisper_model
        audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        
        result = transcriber.transcribe(audio)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_transcribe_calls_progress_callback(self, mock_whisper_model):
        """Test that transcribe calls progress callback."""
        transcriber = Transcriber()
        transcriber.model = mock_whisper_model
        audio = np.zeros(16000, dtype=np.float32)
        
        progress_calls = []
        def on_progress(progress, duration):
            progress_calls.append((progress, duration))
        
        transcriber.transcribe(audio, on_progress=on_progress)
        
        assert len(progress_calls) > 0
        # Final progress should be 100
        assert progress_calls[-1][0] == 100.0


class TestDownloadModel:
    """Tests for the download_model function."""
    
    def test_download_model_calls_progress(self, mock_hf_api, temp_model_dir: Path):
        """Test that download_model calls progress callback."""
        progress_calls = []
        
        def on_progress(percent, message):
            progress_calls.append((percent, message))
        
        download_model("tiny", on_progress=on_progress)
        
        assert len(progress_calls) > 0
        # Should start with 0
        assert progress_calls[0][0] == 0
        # Should end with 100
        assert progress_calls[-1][0] == 100
    
    def test_download_model_handles_error(self, monkeypatch, temp_model_dir: Path):
        """Test that download_model handles errors gracefully."""
        # Mock HfApi to raise an error
        def mock_repo_info(*args, **kwargs):
            raise Exception("Network error")
        
        mock_api = MagicMock()
        mock_api.repo_info = mock_repo_info
        monkeypatch.setattr("local_whisper.transcriber.HfApi", lambda: mock_api)
        
        progress_calls = []
        def on_progress(percent, message):
            progress_calls.append((percent, message))
        
        with pytest.raises(Exception, match="Network error"):
            download_model("tiny", on_progress=on_progress)
        
        # Should have reported error via progress
        assert any(p[0] == -1 for p in progress_calls)


class TestTranscriberAvailableModels:
    """Tests for AVAILABLE_MODELS constant."""
    
    def test_available_models_contains_expected_models(self):
        """Test that AVAILABLE_MODELS contains expected model names."""
        models = Transcriber.get_available_models()
        model_names = [m['name'] for m in models]
        
        expected = ["tiny", "base", "small", "medium", "large-v3"]
        assert model_names == expected
    
    def test_available_models_have_display_names(self):
        """Test that all models have display names."""
        models = Transcriber.get_available_models()
        
        for model in models:
            assert "display_name" in model
            assert "OpenAI Whisper" in model["display_name"]
    
    def test_available_models_have_sizes(self):
        """Test that all models have size information."""
        models = Transcriber.get_available_models()
        
        for model in models:
            assert "size" in model
            assert "~" in model["size"]  # e.g., "~150 MB"

