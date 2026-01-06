"""Tests for the text_output module."""

import pytest
from unittest.mock import MagicMock, patch
import time

from local_whisper.text_output import TextOutput


class TestTextOutputInit:
    """Tests for TextOutput initialization."""
    
    def test_init_default_interval(self, mock_pyautogui):
        """Test default typing interval."""
        output = TextOutput()
        
        assert output.typing_interval == 0.01
    
    def test_init_custom_interval(self, mock_pyautogui):
        """Test custom typing interval."""
        output = TextOutput(typing_interval=0.05)
        
        assert output.typing_interval == 0.05
    
    def test_init_disables_failsafe(self, monkeypatch):
        """Test that FAILSAFE is disabled on init."""
        import pyautogui
        
        # Set FAILSAFE to True initially
        monkeypatch.setattr(pyautogui, "FAILSAFE", True)
        
        output = TextOutput()
        
        assert pyautogui.FAILSAFE is False


class TestTypeText:
    """Tests for type_text method."""
    
    def test_type_text_calls_write(self, mock_pyautogui):
        """Test that type_text calls pyautogui.write."""
        output = TextOutput()
        
        output.type_text("Hello World")
        
        mock_pyautogui.write.assert_called_once()
        call_args = mock_pyautogui.write.call_args
        assert call_args[0][0] == "Hello World"
    
    def test_type_text_uses_interval(self, mock_pyautogui):
        """Test that type_text uses typing interval."""
        output = TextOutput(typing_interval=0.02)
        
        output.type_text("Test")
        
        call_kwargs = mock_pyautogui.write.call_args[1]
        assert call_kwargs['interval'] == 0.02
    
    def test_type_text_empty_string(self, mock_pyautogui):
        """Test that type_text handles empty string."""
        output = TextOutput()
        
        output.type_text("")
        
        # Should not call write for empty string
        mock_pyautogui.write.assert_not_called()
    
    def test_type_text_none_string(self, mock_pyautogui):
        """Test that type_text handles None-like empty string."""
        output = TextOutput()
        
        # Passing falsy value should skip
        output.type_text("")
        
        mock_pyautogui.write.assert_not_called()
    
    def test_type_text_with_unicode(self, mock_pyautogui):
        """Test that type_text handles unicode characters."""
        output = TextOutput()
        
        output.type_text("Hëllo Wörld 日本語")
        
        mock_pyautogui.write.assert_called_once()
        assert mock_pyautogui.typed_texts[-1] == "Hëllo Wörld 日本語"
    
    def test_type_text_default_delay(self, mock_pyautogui, monkeypatch):
        """Test that type_text has default delay before typing."""
        output = TextOutput()
        
        # Track sleep calls
        sleep_calls = []
        original_sleep = time.sleep
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        monkeypatch.setattr(time, "sleep", mock_sleep)
        
        output.type_text("Test")
        
        # Should have slept before typing
        assert 0.1 in sleep_calls
    
    def test_type_text_custom_delay(self, mock_pyautogui, monkeypatch):
        """Test that type_text respects custom delay."""
        output = TextOutput()
        
        sleep_calls = []
        def mock_sleep(duration):
            sleep_calls.append(duration)
        
        monkeypatch.setattr(time, "sleep", mock_sleep)
        
        output.type_text("Test", delay_before=0.5)
        
        assert 0.5 in sleep_calls


class TestTypeTextFast:
    """Tests for type_text_fast method."""
    
    def test_type_text_fast_calls_write(self, mock_pyautogui):
        """Test that type_text_fast calls pyautogui.write."""
        output = TextOutput()
        
        output.type_text_fast("Fast typing")
        
        mock_pyautogui.write.assert_called_once()
    
    def test_type_text_fast_uses_low_interval(self, mock_pyautogui):
        """Test that type_text_fast uses very low interval."""
        output = TextOutput()
        
        output.type_text_fast("Fast")
        
        call_kwargs = mock_pyautogui.write.call_args[1]
        assert call_kwargs['interval'] == 0.001
    
    def test_type_text_fast_empty_string(self, mock_pyautogui):
        """Test that type_text_fast handles empty string."""
        output = TextOutput()
        
        output.type_text_fast("")
        
        mock_pyautogui.write.assert_not_called()


class TestPressKey:
    """Tests for press_key static method."""
    
    def test_press_key_calls_press(self, mock_pyautogui):
        """Test that press_key calls pyautogui.press."""
        TextOutput.press_key("enter")
        
        mock_pyautogui.press.assert_called_once_with("enter")
    
    def test_press_key_various_keys(self, mock_pyautogui):
        """Test pressing various keys."""
        keys = ["enter", "tab", "backspace", "escape", "space"]
        
        for key in keys:
            mock_pyautogui.press.reset_mock()
            TextOutput.press_key(key)
            mock_pyautogui.press.assert_called_once_with(key)


class TestHotkey:
    """Tests for hotkey static method."""
    
    def test_hotkey_calls_hotkey(self, mock_pyautogui):
        """Test that hotkey calls pyautogui.hotkey."""
        TextOutput.hotkey("ctrl", "v")
        
        mock_pyautogui.hotkey.assert_called_once()
    
    def test_hotkey_passes_all_keys(self, mock_pyautogui):
        """Test that hotkey passes all keys."""
        TextOutput.hotkey("ctrl", "shift", "a")
        
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "shift", "a")
    
    def test_hotkey_common_combinations(self, mock_pyautogui):
        """Test common hotkey combinations."""
        combinations = [
            ("ctrl", "c"),
            ("ctrl", "v"),
            ("ctrl", "z"),
            ("alt", "tab"),
            ("ctrl", "shift", "esc"),
        ]
        
        for combo in combinations:
            mock_pyautogui.hotkey.reset_mock()
            TextOutput.hotkey(*combo)
            mock_pyautogui.hotkey.assert_called_once_with(*combo)

