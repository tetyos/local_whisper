"""Tests for the hotkey_handler module."""

import pytest
from unittest.mock import MagicMock, patch
import threading
import time

from local_whisper.hotkey_handler import HotkeyHandler


class TestHotkeyHandlerInit:
    """Tests for HotkeyHandler initialization."""
    
    def test_init_default_hotkey(self):
        """Test default hotkey is ctrl+space."""
        handler = HotkeyHandler()
        
        assert handler.hotkey == "ctrl+space"
    
    def test_init_custom_hotkey(self):
        """Test custom hotkey."""
        handler = HotkeyHandler(hotkey="alt+r")
        
        assert handler.hotkey == "alt+r"
    
    def test_init_not_registered(self):
        """Test that handler is not registered initially."""
        handler = HotkeyHandler()
        
        assert handler.is_registered() is False
        assert handler._callback is None


class TestHotkeyRegistration:
    """Tests for hotkey registration."""
    
    def test_register_sets_callback(self, mock_keyboard):
        """Test that register sets the callback."""
        handler = HotkeyHandler()
        callback = MagicMock()
        
        handler.register(callback)
        
        assert handler._callback == callback
    
    def test_register_calls_keyboard_add_hotkey(self, mock_keyboard):
        """Test that register calls keyboard.add_hotkey."""
        handler = HotkeyHandler()
        callback = MagicMock()
        
        handler.register(callback)
        
        mock_keyboard.add_hotkey.assert_called_once()
        call_args = mock_keyboard.add_hotkey.call_args
        assert call_args[0][0] == "ctrl+space"
    
    def test_register_sets_registered_flag(self, mock_keyboard):
        """Test that register sets the registered flag."""
        handler = HotkeyHandler()
        
        handler.register(MagicMock())
        
        assert handler.is_registered() is True
    
    def test_register_unregisters_first_if_already_registered(self, mock_keyboard):
        """Test that register unregisters first if already registered."""
        handler = HotkeyHandler()
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        handler.register(callback1)
        handler.register(callback2)
        
        # Should have been called twice (once per register)
        assert mock_keyboard.add_hotkey.call_count == 2
        # Callback should be updated
        assert handler._callback == callback2


class TestHotkeyUnregistration:
    """Tests for hotkey unregistration."""
    
    def test_unregister_calls_keyboard_remove_hotkey(self, mock_keyboard):
        """Test that unregister calls keyboard.remove_hotkey."""
        handler = HotkeyHandler()
        handler.register(MagicMock())
        
        handler.unregister()
        
        mock_keyboard.remove_hotkey.assert_called_once_with("ctrl+space")
    
    def test_unregister_clears_callback(self, mock_keyboard):
        """Test that unregister clears the callback."""
        handler = HotkeyHandler()
        handler.register(MagicMock())
        
        handler.unregister()
        
        assert handler._callback is None
    
    def test_unregister_clears_registered_flag(self, mock_keyboard):
        """Test that unregister clears the registered flag."""
        handler = HotkeyHandler()
        handler.register(MagicMock())
        
        handler.unregister()
        
        assert handler.is_registered() is False
    
    def test_unregister_when_not_registered(self, mock_keyboard):
        """Test that unregister does nothing when not registered."""
        handler = HotkeyHandler()
        
        # Should not raise
        handler.unregister()
        
        mock_keyboard.remove_hotkey.assert_not_called()
    
    def test_unregister_handles_key_error(self, mock_keyboard):
        """Test that unregister handles KeyError gracefully."""
        handler = HotkeyHandler()
        handler.register(MagicMock())
        
        # Simulate hotkey already removed
        handler._registered = True
        mock_keyboard._registered_hotkeys.clear()
        
        # Should not raise
        handler.unregister()
        
        assert handler.is_registered() is False


class TestHotkeyCallback:
    """Tests for hotkey callback execution."""
    
    def test_callback_is_called_in_thread(self, mock_keyboard):
        """Test that callback is executed in a separate thread."""
        handler = HotkeyHandler()
        callback = MagicMock()
        
        handler.register(callback)
        
        # Simulate hotkey press by calling the internal handler
        handler._on_hotkey_pressed()
        
        # Give thread time to start
        time.sleep(0.1)
        
        callback.assert_called_once()
    
    def test_callback_not_called_when_none(self, mock_keyboard):
        """Test that no error when callback is None."""
        handler = HotkeyHandler()
        handler._callback = None
        
        # Should not raise
        handler._on_hotkey_pressed()


class TestGetHotkeyDisplay:
    """Tests for get_hotkey_display method."""
    
    def test_formats_ctrl_space(self):
        """Test formatting of ctrl+space."""
        handler = HotkeyHandler(hotkey="ctrl+space")
        
        result = handler.get_hotkey_display()
        
        assert result == "Ctrl + Space"
    
    def test_formats_alt_r(self):
        """Test formatting of alt+r."""
        handler = HotkeyHandler(hotkey="alt+r")
        
        result = handler.get_hotkey_display()
        
        assert result == "Alt + R"
    
    def test_formats_complex_hotkey(self):
        """Test formatting of complex hotkey."""
        handler = HotkeyHandler(hotkey="ctrl+shift+a")
        
        result = handler.get_hotkey_display()
        
        assert result == "Ctrl + Shift + A"


class TestThreadSafety:
    """Tests for thread safety of HotkeyHandler."""
    
    def test_is_registered_uses_lock(self, mock_keyboard):
        """Test that is_registered uses lock."""
        handler = HotkeyHandler()
        
        # Verify lock exists
        assert hasattr(handler, '_lock')
        # Check it behaves like a lock (has acquire/release)
        assert hasattr(handler._lock, 'acquire')
        assert hasattr(handler._lock, 'release')
    
    def test_register_uses_lock(self, mock_keyboard):
        """Test that register uses lock."""
        handler = HotkeyHandler()
        
        # This should work without deadlock
        handler.register(MagicMock())
        
        assert handler.is_registered()
    
    def test_unregister_uses_lock(self, mock_keyboard):
        """Test that unregister uses lock."""
        handler = HotkeyHandler()
        handler.register(MagicMock())
        
        # This should work without deadlock
        handler.unregister()
        
        assert not handler.is_registered()

