"""Text output module for typing text into the active window."""

import pyautogui
import time


class TextOutput:
    """Types text into the currently active window."""
    
    def __init__(self, typing_interval: float = 0.01):
        """
        Initialize the text output handler.
        
        Args:
            typing_interval: Delay between keystrokes in seconds
        """
        self.typing_interval = typing_interval
        # Disable pyautogui failsafe (move mouse to corner to abort)
        # We handle this differently in our app
        pyautogui.FAILSAFE = False
    
    def type_text(self, text: str, delay_before: float = 0.1) -> None:
        """
        Type text into the currently active window.
        
        Args:
            text: The text to type
            delay_before: Delay before starting to type (allows window focus)
        """
        if not text:
            return
        
        # Small delay to ensure the target window is focused
        time.sleep(delay_before)
        
        # Use typewrite for ASCII characters, but we need write() for unicode
        # pyautogui.write() handles unicode better
        pyautogui.write(text, interval=self.typing_interval)
    
    def type_text_fast(self, text: str, delay_before: float = 0.1) -> None:
        """
        Type text quickly using clipboard-like behavior.
        This is faster but may not work in all applications.
        
        Args:
            text: The text to type
            delay_before: Delay before starting to type
        """
        if not text:
            return
        
        time.sleep(delay_before)
        
        # For faster typing, use hotkey with lower interval
        pyautogui.write(text, interval=0.001)
    
    @staticmethod
    def press_key(key: str) -> None:
        """
        Press a single key.
        
        Args:
            key: The key to press (e.g., 'enter', 'tab', 'backspace')
        """
        pyautogui.press(key)
    
    @staticmethod
    def hotkey(*keys: str) -> None:
        """
        Press a hotkey combination.
        
        Args:
            keys: Keys to press simultaneously (e.g., 'ctrl', 'v')
        """
        pyautogui.hotkey(*keys)

