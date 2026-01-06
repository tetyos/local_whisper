"""Global hotkey handler for Ctrl+Space detection."""

import keyboard
from typing import Callable, Optional
import threading


class HotkeyHandler:
    """Handles global hotkey registration and callbacks."""
    
    def __init__(self, hotkey: str = "ctrl+space"):
        """
        Initialize the hotkey handler.
        
        Args:
            hotkey: The hotkey combination to listen for
        """
        self.hotkey = hotkey
        self._callback: Optional[Callable[[], None]] = None
        self._registered = False
        self._lock = threading.RLock()
    
    def register(self, callback: Callable[[], None]) -> None:
        """
        Register a callback function for the hotkey.
        
        Args:
            callback: Function to call when hotkey is pressed
        """
        with self._lock:
            if self._registered:
                self.unregister()
            
            self._callback = callback
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_pressed, suppress=False)
            self._registered = True
    
    def _on_hotkey_pressed(self) -> None:
        """Internal handler for hotkey press."""
        if self._callback is not None:
            # Run callback in a separate thread to avoid blocking
            threading.Thread(target=self._callback, daemon=True).start()
    
    def unregister(self) -> None:
        """Unregister the hotkey."""
        with self._lock:
            if self._registered:
                try:
                    keyboard.remove_hotkey(self.hotkey)
                except KeyError:
                    pass  # Hotkey was already removed
                self._registered = False
                self._callback = None
    
    def is_registered(self) -> bool:
        """Check if the hotkey is currently registered."""
        with self._lock:
            return self._registered
    
    def get_hotkey_display(self) -> str:
        """Get a human-readable display string for the hotkey."""
        return self.hotkey.replace("+", " + ").title()

