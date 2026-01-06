"""Tests for the settings module."""

import json
import pytest
from pathlib import Path

from local_whisper.settings import (
    get_settings_directory,
    get_settings_path,
    get_transcription_stats_path,
    get_default_settings,
    load_settings,
    save_settings,
    get_selected_model,
    set_selected_model,
    load_transcription_stats,
    save_transcription_stats,
    record_transcription_time,
    get_estimated_transcription_time,
)


class TestSettingsDirectory:
    """Tests for settings directory functions."""
    
    def test_get_settings_directory_creates_dir(self, temp_settings_dir: Path):
        """Test that get_settings_directory creates the directory if it doesn't exist."""
        # Remove the directory to test creation
        import shutil
        if temp_settings_dir.exists():
            shutil.rmtree(temp_settings_dir)
        
        result = get_settings_directory()
        
        assert result.exists()
        assert result.is_dir()
        assert result.name == "local-whisper"
    
    def test_get_settings_path(self, temp_settings_dir: Path):
        """Test that get_settings_path returns correct path."""
        result = get_settings_path()
        
        assert result.name == "settings.json"
        assert result.parent.name == "local-whisper"
    
    def test_get_transcription_stats_path(self, temp_settings_dir: Path):
        """Test that get_transcription_stats_path returns correct path."""
        result = get_transcription_stats_path()
        
        assert result.name == "transcription_stats.json"
        assert result.parent.name == "local-whisper"


class TestDefaultSettings:
    """Tests for default settings."""
    
    def test_get_default_settings_returns_dict(self):
        """Test that get_default_settings returns a dictionary."""
        result = get_default_settings()
        
        assert isinstance(result, dict)
    
    def test_get_default_settings_has_selected_model(self):
        """Test that default settings include selected_model."""
        result = get_default_settings()
        
        assert "selected_model" in result
        assert result["selected_model"] == "base"


class TestLoadSaveSettings:
    """Tests for loading and saving settings."""
    
    def test_load_settings_returns_defaults_when_no_file(self, temp_settings_dir: Path):
        """Test that load_settings returns defaults when file doesn't exist."""
        result = load_settings()
        
        assert result == get_default_settings()
    
    def test_save_and_load_settings(self, temp_settings_dir: Path):
        """Test that settings can be saved and loaded."""
        test_settings = {"selected_model": "small", "custom_key": "custom_value"}
        
        save_settings(test_settings)
        result = load_settings()
        
        assert result["selected_model"] == "small"
        assert result["custom_key"] == "custom_value"
    
    def test_load_settings_merges_with_defaults(self, temp_settings_dir: Path):
        """Test that loaded settings are merged with defaults."""
        # Save settings without selected_model
        settings_path = get_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump({"custom_key": "value"}, f)
        
        result = load_settings()
        
        # Should have both default and custom keys
        assert "selected_model" in result  # from defaults
        assert "custom_key" in result  # from file
    
    def test_load_settings_handles_invalid_json(self, temp_settings_dir: Path):
        """Test that load_settings handles corrupted JSON gracefully."""
        settings_path = get_settings_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write("not valid json {{{")
        
        result = load_settings()
        
        assert result == get_default_settings()


class TestSelectedModel:
    """Tests for selected model getter/setter."""
    
    def test_get_selected_model_returns_default(self, temp_settings_dir: Path):
        """Test that get_selected_model returns default when no settings."""
        result = get_selected_model()
        
        assert result == "base"
    
    def test_set_and_get_selected_model(self, temp_settings_dir: Path):
        """Test that selected model can be set and retrieved."""
        set_selected_model("large-v3")
        result = get_selected_model()
        
        assert result == "large-v3"
    
    def test_set_selected_model_persists(self, temp_settings_dir: Path):
        """Test that selected model persists across calls."""
        set_selected_model("medium")
        
        # Verify it's saved to file
        settings_path = get_settings_path()
        with open(settings_path, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        
        assert saved["selected_model"] == "medium"


class TestTranscriptionStats:
    """Tests for transcription statistics functions."""
    
    def test_load_transcription_stats_returns_empty_when_no_file(self, temp_settings_dir: Path):
        """Test that load_transcription_stats returns empty dict when no file."""
        result = load_transcription_stats()
        
        assert result == {}
    
    def test_save_and_load_transcription_stats(self, temp_settings_dir: Path):
        """Test that transcription stats can be saved and loaded."""
        test_stats = {
            "base": {
                "samples": [{"audio_duration": 5.0, "transcription_time": 2.5}],
                "avg_ratio": 0.5
            }
        }
        
        save_transcription_stats(test_stats)
        result = load_transcription_stats()
        
        assert result == test_stats
    
    def test_load_transcription_stats_handles_invalid_json(self, temp_settings_dir: Path):
        """Test that load_transcription_stats handles corrupted JSON."""
        stats_path = get_transcription_stats_path()
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write("invalid json")
        
        result = load_transcription_stats()
        
        assert result == {}


class TestRecordTranscriptionTime:
    """Tests for recording transcription times."""
    
    def test_record_transcription_time_creates_new_model_entry(self, temp_settings_dir: Path):
        """Test that recording time creates new model entry."""
        record_transcription_time("tiny", audio_duration=10.0, transcription_time=3.0)
        
        stats = load_transcription_stats()
        
        assert "tiny" in stats
        assert len(stats["tiny"]["samples"]) == 1
        assert stats["tiny"]["samples"][0]["audio_duration"] == 10.0
        assert stats["tiny"]["samples"][0]["transcription_time"] == 3.0
    
    def test_record_transcription_time_calculates_avg_ratio(self, temp_settings_dir: Path):
        """Test that average ratio is calculated correctly."""
        record_transcription_time("base", audio_duration=10.0, transcription_time=5.0)
        record_transcription_time("base", audio_duration=20.0, transcription_time=10.0)
        
        stats = load_transcription_stats()
        
        # avg_ratio = (5 + 10) / (10 + 20) = 15/30 = 0.5
        assert stats["base"]["avg_ratio"] == pytest.approx(0.5)
    
    def test_record_transcription_time_limits_to_20_samples(self, temp_settings_dir: Path):
        """Test that only last 20 samples are kept."""
        for i in range(25):
            record_transcription_time("small", audio_duration=10.0, transcription_time=5.0)
        
        stats = load_transcription_stats()
        
        assert len(stats["small"]["samples"]) == 20


class TestGetEstimatedTranscriptionTime:
    """Tests for transcription time estimation."""
    
    def test_uses_historical_data_when_available(self, temp_settings_dir: Path):
        """Test that estimation uses historical data when available."""
        # Record some history
        record_transcription_time("base", audio_duration=10.0, transcription_time=5.0)
        
        # Estimate for 20 seconds of audio
        result = get_estimated_transcription_time("base", audio_duration=20.0)
        
        # With ratio 0.5, estimate should be 10.0
        assert result == pytest.approx(10.0)
    
    def test_uses_default_ratio_for_tiny(self, temp_settings_dir: Path):
        """Test default ratio for tiny model."""
        result = get_estimated_transcription_time("tiny", audio_duration=10.0)
        
        # Default ratio for tiny is 0.3
        assert result == pytest.approx(3.0)
    
    def test_uses_default_ratio_for_base(self, temp_settings_dir: Path):
        """Test default ratio for base model."""
        result = get_estimated_transcription_time("base", audio_duration=10.0)
        
        # Default ratio for base is 0.5
        assert result == pytest.approx(5.0)
    
    def test_uses_default_ratio_for_small(self, temp_settings_dir: Path):
        """Test default ratio for small model."""
        result = get_estimated_transcription_time("small", audio_duration=10.0)
        
        # Default ratio for small is 1.0
        assert result == pytest.approx(10.0)
    
    def test_uses_default_ratio_for_medium(self, temp_settings_dir: Path):
        """Test default ratio for medium model."""
        result = get_estimated_transcription_time("medium", audio_duration=10.0)
        
        # Default ratio for medium is 2.5
        assert result == pytest.approx(25.0)
    
    def test_uses_default_ratio_for_large(self, temp_settings_dir: Path):
        """Test default ratio for large-v3 model."""
        result = get_estimated_transcription_time("large-v3", audio_duration=10.0)
        
        # Default ratio for large-v3 is 5.0
        assert result == pytest.approx(50.0)
    
    def test_uses_fallback_ratio_for_unknown_model(self, temp_settings_dir: Path):
        """Test fallback ratio for unknown model."""
        result = get_estimated_transcription_time("unknown-model", audio_duration=10.0)
        
        # Default fallback ratio is 1.0
        assert result == pytest.approx(10.0)

