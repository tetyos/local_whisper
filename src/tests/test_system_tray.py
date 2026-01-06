"""Tests for the system_tray UI module."""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtGui import QIcon

from local_whisper.ui.system_tray import SystemTray, create_tray_icon


class TestCreateTrayIcon:
    """Tests for create_tray_icon function."""
    
    def test_returns_qicon(self, qtbot):
        """Test that function returns a QIcon."""
        icon = create_tray_icon()
        
        assert isinstance(icon, QIcon)
    
    def test_idle_icon_is_not_null(self, qtbot):
        """Test that idle icon is not null."""
        icon = create_tray_icon(recording=False)
        
        assert not icon.isNull()
    
    def test_recording_icon_is_not_null(self, qtbot):
        """Test that recording icon is not null."""
        icon = create_tray_icon(recording=True)
        
        assert not icon.isNull()
    
    def test_idle_and_recording_icons_are_different(self, qtbot):
        """Test that idle and recording icons are visually different."""
        idle_icon = create_tray_icon(recording=False)
        recording_icon = create_tray_icon(recording=True)
        
        # Get the pixmaps to compare
        idle_pixmap = idle_icon.pixmap(64, 64)
        recording_pixmap = recording_icon.pixmap(64, 64)
        
        # Convert to images for comparison
        idle_image = idle_pixmap.toImage()
        recording_image = recording_pixmap.toImage()
        
        # They should be different (different colors)
        assert idle_image != recording_image


class TestSystemTrayInit:
    """Tests for SystemTray initialization."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_has_icon(self, system_tray):
        """Test that tray has an icon."""
        assert not system_tray.icon().isNull()
    
    def test_has_tooltip(self, system_tray):
        """Test that tray has a tooltip."""
        tooltip = system_tray.toolTip()
        
        assert "local-whisper" in tooltip
        assert "Ctrl" in tooltip or "Space" in tooltip
    
    def test_has_context_menu(self, system_tray):
        """Test that tray has a context menu."""
        menu = system_tray.contextMenu()
        
        assert menu is not None
        assert isinstance(menu, QMenu)


class TestSystemTrayMenu:
    """Tests for system tray context menu."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_menu_has_show_action(self, system_tray):
        """Test that menu has 'Show Window' action."""
        menu = system_tray.contextMenu()
        actions = menu.actions()
        
        action_texts = [a.text() for a in actions]
        assert any("Show" in text for text in action_texts)
    
    def test_menu_has_exit_action(self, system_tray):
        """Test that menu has 'Exit' action."""
        menu = system_tray.contextMenu()
        actions = menu.actions()
        
        action_texts = [a.text() for a in actions]
        assert any("Exit" in text for text in action_texts)
    
    def test_menu_has_separator(self, system_tray):
        """Test that menu has a separator."""
        menu = system_tray.contextMenu()
        actions = menu.actions()
        
        has_separator = any(a.isSeparator() for a in actions)
        assert has_separator


class TestSystemTraySignals:
    """Tests for system tray signals."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_show_window_signal_exists(self, system_tray):
        """Test that show_window_requested signal exists."""
        assert hasattr(system_tray, 'show_window_requested')
    
    def test_exit_signal_exists(self, system_tray):
        """Test that exit_requested signal exists."""
        assert hasattr(system_tray, 'exit_requested')
    
    def test_show_action_emits_signal(self, system_tray, qtbot):
        """Test that Show Window action emits signal."""
        menu = system_tray.contextMenu()
        show_action = None
        for action in menu.actions():
            if "Show" in action.text():
                show_action = action
                break
        
        assert show_action is not None
        
        with qtbot.waitSignal(system_tray.show_window_requested, timeout=1000):
            show_action.trigger()
    
    def test_exit_action_emits_signal(self, system_tray, qtbot):
        """Test that Exit action emits signal."""
        menu = system_tray.contextMenu()
        exit_action = None
        for action in menu.actions():
            if "Exit" in action.text():
                exit_action = action
                break
        
        assert exit_action is not None
        
        with qtbot.waitSignal(system_tray.exit_requested, timeout=1000):
            exit_action.trigger()


class TestSystemTrayRecordingState:
    """Tests for recording state changes."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_set_recording_true_changes_icon(self, system_tray):
        """Test that set_recording(True) changes the icon."""
        initial_icon = system_tray.icon()
        
        system_tray.set_recording(True)
        
        new_icon = system_tray.icon()
        # Icons should be different (visually)
        initial_pixmap = initial_icon.pixmap(64, 64).toImage()
        new_pixmap = new_icon.pixmap(64, 64).toImage()
        assert initial_pixmap != new_pixmap
    
    def test_set_recording_false_changes_icon(self, system_tray):
        """Test that set_recording(False) changes the icon back."""
        system_tray.set_recording(True)
        recording_icon = system_tray.icon()
        
        system_tray.set_recording(False)
        
        idle_icon = system_tray.icon()
        # Icons should be different
        recording_pixmap = recording_icon.pixmap(64, 64).toImage()
        idle_pixmap = idle_icon.pixmap(64, 64).toImage()
        assert recording_pixmap != idle_pixmap
    
    def test_set_recording_updates_tooltip(self, system_tray):
        """Test that set_recording updates tooltip."""
        system_tray.set_recording(True)
        recording_tooltip = system_tray.toolTip()
        
        system_tray.set_recording(False)
        idle_tooltip = system_tray.toolTip()
        
        # Tooltips should be different
        assert recording_tooltip != idle_tooltip
        assert "Recording" in recording_tooltip or "stop" in recording_tooltip.lower()
        assert "record" in idle_tooltip.lower()


class TestSystemTrayShowMessage:
    """Tests for show_message method."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_show_message_method_exists(self, system_tray):
        """Test that show_message method exists."""
        assert hasattr(system_tray, 'show_message')
        assert callable(system_tray.show_message)
    
    def test_show_message_calls_showMessage(self, system_tray, qtbot, monkeypatch):
        """Test that show_message calls QSystemTrayIcon.showMessage."""
        # Track if showMessage was called
        call_args = []
        def mock_show_message(title, message, icon, duration):
            call_args.append((title, message, icon, duration))
        
        monkeypatch.setattr(system_tray, "showMessage", mock_show_message)
        
        from PyQt6.QtWidgets import QSystemTrayIcon
        system_tray.show_message("Test Title", "Test Message")
        
        assert len(call_args) == 1
        assert call_args[0][0] == "Test Title"
        assert call_args[0][1] == "Test Message"


class TestSystemTrayDoubleClick:
    """Tests for double-click behavior."""
    
    @pytest.fixture
    def system_tray(self, qtbot):
        """Create a SystemTray instance for testing."""
        tray = SystemTray()
        return tray
    
    def test_double_click_emits_show_signal(self, system_tray, qtbot):
        """Test that double-click emits show_window_requested signal."""
        from PyQt6.QtWidgets import QSystemTrayIcon
        
        with qtbot.waitSignal(system_tray.show_window_requested, timeout=1000):
            system_tray._on_activated(QSystemTrayIcon.ActivationReason.DoubleClick)
    
    def test_single_click_does_not_emit_signal(self, system_tray, qtbot):
        """Test that single click does not emit show signal."""
        from PyQt6.QtWidgets import QSystemTrayIcon
        
        # Connect a tracker
        signals_received = []
        system_tray.show_window_requested.connect(lambda: signals_received.append(True))
        
        system_tray._on_activated(QSystemTrayIcon.ActivationReason.Trigger)
        
        # Give it a moment
        qtbot.wait(100)
        
        assert len(signals_received) == 0

