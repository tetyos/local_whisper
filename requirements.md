# Luca Whisper - Requirements Specification

## Overview

Luca Whisper is a Windows speech-to-text (STT) application that allows users to dictate text directly into any active window using a global hotkey.

## Functional Requirements

### FR-1: Speech-to-Text Conversion
- The application shall use the Whisper AI model (base variant, ~150MB) for speech recognition
- The model shall be downloaded automatically on first run to `%APPDATA%/luca-whisper/models/`
- Transcription shall support multiple languages (Whisper's default language detection)

### FR-2: Hotkey Activation
- The application shall respond to `Ctrl+Space` as a global hotkey
- First press: Start recording audio from the default microphone
- Second press: Stop recording and begin transcription
- The hotkey shall work regardless of which application is in focus

### FR-3: Text Output
- Transcribed text shall be typed directly into the currently active window
- Text shall be inserted at the current cursor position
- The application shall simulate keyboard input (not clipboard paste)

### FR-4: User Interface
- Display program name "luca-whisper" prominently
- Show current status: idle, recording, or transcribing
- Display the hotkey shortcut `Ctrl+Space` for user reference
- Visual indicator when recording is active (e.g., recording icon or status text)

### FR-5: System Tray Integration
- The application shall minimize to the Windows system tray when closed
- System tray icon shall provide right-click context menu with:
  - "Show Window" - Restore the main window
  - "Exit" - Completely close the application
- The tray icon shall indicate current status (idle/recording)

### FR-6: Windows Integration
- The application shall be visible in Windows Task Manager when running
- The application shall be installable via a standalone `.exe` file
- No external dependencies required for end users (bundled with PyInstaller)

## Non-Functional Requirements

### NFR-1: Performance
- Audio recording shall start within 200ms of hotkey press
- Transcription time shall be reasonable for the audio length (faster-whisper optimized)

### NFR-2: Compatibility
- Windows 10 and Windows 11 support
- Python 3.11+ for development

### NFR-3: Licensing
- All components must be open source and free for commercial use
- Whisper model: MIT License
- faster-whisper: MIT License
- All Python dependencies: MIT/BSD compatible

## Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Development language |
| STT Model | faster-whisper (base) | Speech recognition |
| Audio | sounddevice + numpy | Microphone capture |
| Hotkey | keyboard | Global hotkey detection |
| UI | PyQt6 | Desktop application UI |
| Text Input | pyautogui | Simulate keyboard input |
| Installer | PyInstaller | Create Windows .exe |

## User Stories

1. **As a user**, I want to press `Ctrl+Space` to start voice recording so that I can dictate text hands-free.

2. **As a user**, I want to press `Ctrl+Space` again to stop recording and have my speech transcribed and typed into my current application.

3. **As a user**, I want the app to run in the system tray so it doesn't clutter my taskbar while remaining accessible.

4. **As a user**, I want to see a visual indicator when recording is active so I know the app is listening.

5. **As a user**, I want to install the app with a single .exe file without needing to install Python or other dependencies.

