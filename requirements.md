# Luca Whisper - Requirements Specification

## Overview

Luca Whisper is a Windows speech-to-text (STT) application that allows users to dictate text directly into any active window using a global hotkey.

## Functional Requirements

### FR-1: Speech-to-Text Conversion
- The application shall use faster-whisper models (optimized versions of OpenAI whisper models) for speech recognition
- Transcription shall use the model which is currently selected by the user (see FR-7: Model Selection)
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

### FR-7: Model Selection
- Users shall be able to choose from all available faster-whisper models equivalents to OpenAI Whisper models (e.g., tiny, base, small, medium, large, large-v2, large-v3)
- Only open-source models shall be available for selection (no proprietary models)
- Models shall be stored in `%APPDATA%/luca-whisper/models/`
- Models shall NOT be automatically downloaded on first run or application start
- A model shall only be downloaded when the user explicitly selects that specific model
- When a model is selected but not yet downloaded, it shall be downloaded automatically with progress indicators displayed (e.g., progress bar, percentage, or download status)
- The user interface shall clearly indicate which models are already downloaded and available locally
- The user interface shall clearly display which model is currently selected
- The currently selected model shall be used for all transcription tasks
- The selected model preference shall persist across application sessions

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
| STT Model | faster-whisper (tiny, base, small, medium, large, large-v2, large-v3) | Speech recognition |
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

