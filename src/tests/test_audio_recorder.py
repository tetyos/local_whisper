"""Tests for the audio_recorder module."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch, call

from local_whisper.audio_recorder import AudioRecorder


class TestAudioRecorderInit:
    """Tests for AudioRecorder initialization."""
    
    def test_init_default_sample_rate(self):
        """Test default sample rate is 16000."""
        recorder = AudioRecorder()
        
        assert recorder.sample_rate == 16000
    
    def test_init_custom_sample_rate(self):
        """Test custom sample rate."""
        recorder = AudioRecorder(sample_rate=44100)
        
        assert recorder.sample_rate == 44100
    
    def test_init_not_recording(self):
        """Test that recorder is not recording initially."""
        recorder = AudioRecorder()
        
        assert recorder.recording is False
        assert recorder.is_recording() is False
    
    def test_init_empty_audio_data(self):
        """Test that audio_data is empty initially."""
        recorder = AudioRecorder()
        
        assert recorder.audio_data == []


class TestAudioRecorderRecording:
    """Tests for recording functionality."""
    
    def test_start_recording_sets_flag(self, mock_sounddevice):
        """Test that start_recording sets recording flag."""
        recorder = AudioRecorder()
        
        recorder.start_recording()
        
        assert recorder.is_recording() is True
    
    def test_start_recording_clears_previous_data(self, mock_sounddevice):
        """Test that start_recording clears previous audio data."""
        recorder = AudioRecorder()
        recorder.audio_data = [np.array([1, 2, 3])]
        
        recorder.start_recording()
        
        assert recorder.audio_data == []
    
    def test_start_recording_creates_stream(self, mock_sounddevice):
        """Test that start_recording creates an InputStream."""
        recorder = AudioRecorder()
        
        recorder.start_recording()
        
        mock_sounddevice.InputStream.assert_called_once()
        # Verify stream parameters
        call_kwargs = mock_sounddevice.InputStream.call_args[1]
        assert call_kwargs['samplerate'] == 16000
        assert call_kwargs['channels'] == 1
        assert call_kwargs['dtype'] == np.float32
    
    def test_start_recording_starts_stream(self, mock_sounddevice):
        """Test that start_recording starts the stream."""
        recorder = AudioRecorder()
        
        recorder.start_recording()
        
        mock_sounddevice.InputStream.return_value.start.assert_called_once()
    
    def test_stop_recording_clears_flag(self, mock_sounddevice):
        """Test that stop_recording clears recording flag."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        recorder.stop_recording()
        
        assert recorder.is_recording() is False
    
    def test_stop_recording_stops_stream(self, mock_sounddevice):
        """Test that stop_recording stops the stream."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        recorder.stop_recording()
        
        mock_stream = mock_sounddevice.InputStream.return_value
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()
    
    def test_stop_recording_returns_empty_when_no_data(self, mock_sounddevice):
        """Test that stop_recording returns empty array when no data."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        result = recorder.stop_recording()
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0
        assert result.dtype == np.float32
    
    def test_stop_recording_concatenates_chunks(self, mock_sounddevice):
        """Test that stop_recording concatenates audio chunks."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        # Simulate audio data being added
        chunk1 = np.array([[0.1], [0.2]], dtype=np.float32)
        chunk2 = np.array([[0.3], [0.4]], dtype=np.float32)
        recorder.audio_data = [chunk1, chunk2]
        
        result = recorder.stop_recording()
        
        assert len(result) == 4
        np.testing.assert_array_almost_equal(result, [0.1, 0.2, 0.3, 0.4])
    
    def test_stop_recording_flattens_to_1d(self, mock_sounddevice):
        """Test that stop_recording returns 1D array."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        # Simulate 2D audio data (channels)
        chunk = np.array([[0.1], [0.2], [0.3]], dtype=np.float32)
        recorder.audio_data = [chunk]
        
        result = recorder.stop_recording()
        
        assert result.ndim == 1
    
    def test_stop_recording_without_start(self, mock_sounddevice):
        """Test that stop_recording works even if not started."""
        recorder = AudioRecorder()
        
        result = recorder.stop_recording()
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0


class TestAudioCallback:
    """Tests for the audio callback function."""
    
    def test_callback_appends_data_when_recording(self, mock_sounddevice):
        """Test that callback appends data when recording."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        # Simulate callback
        test_data = np.array([[0.5], [0.6]], dtype=np.float32)
        recorder._audio_callback(test_data, 2, {}, None)
        
        assert len(recorder.audio_data) == 1
        np.testing.assert_array_equal(recorder.audio_data[0], test_data)
    
    def test_callback_ignores_data_when_not_recording(self, mock_sounddevice):
        """Test that callback ignores data when not recording."""
        recorder = AudioRecorder()
        # Don't start recording
        
        test_data = np.array([[0.5]], dtype=np.float32)
        recorder._audio_callback(test_data, 1, {}, None)
        
        assert len(recorder.audio_data) == 0
    
    def test_callback_copies_data(self, mock_sounddevice):
        """Test that callback copies input data."""
        recorder = AudioRecorder()
        recorder.start_recording()
        
        test_data = np.array([[0.5]], dtype=np.float32)
        recorder._audio_callback(test_data, 1, {}, None)
        
        # Modify original data
        test_data[0, 0] = 0.9
        
        # Recorded data should be unchanged
        assert recorder.audio_data[0][0, 0] == 0.5


class TestGetAvailableDevices:
    """Tests for get_available_devices static method."""
    
    def test_returns_input_devices_only(self, mock_sounddevice):
        """Test that only input devices are returned."""
        result = AudioRecorder.get_available_devices()
        
        assert len(result) == 1
        assert result[0]['name'] == 'Test Microphone'
    
    def test_device_info_structure(self, mock_sounddevice):
        """Test the structure of returned device info."""
        result = AudioRecorder.get_available_devices()
        
        device = result[0]
        assert 'index' in device
        assert 'name' in device
        assert 'channels' in device
        assert 'sample_rate' in device
    
    def test_empty_when_no_input_devices(self, monkeypatch):
        """Test returns empty list when no input devices."""
        mock_sd = MagicMock()
        mock_sd.query_devices.return_value = [
            {'name': 'Speaker', 'max_input_channels': 0, 'max_output_channels': 2, 'default_samplerate': 44100}
        ]
        monkeypatch.setattr("sounddevice.query_devices", mock_sd.query_devices)
        
        result = AudioRecorder.get_available_devices()
        
        assert result == []


class TestIsRecording:
    """Tests for is_recording method."""
    
    def test_is_recording_thread_safe(self, mock_sounddevice):
        """Test that is_recording uses lock for thread safety."""
        recorder = AudioRecorder()
        
        # This should not raise even with threading
        assert recorder.is_recording() is False
        
        recorder.start_recording()
        assert recorder.is_recording() is True
        
        recorder.stop_recording()
        assert recorder.is_recording() is False

