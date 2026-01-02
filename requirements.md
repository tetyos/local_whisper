# Local Whisper - Requirements Specification

## Overview

Local Whisper is a Windows speech-to-text (STT) application that allows users to dictate text directly into any active window using a global hotkey.

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
- Display program name "local-whisper" prominently
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
- Users shall be able to choose from all available faster-whisper models equivalents to OpenAI Whisper models (e.g., tiny, base, small, medium, large-v3)
- Only open-source models shall be available for selection (no proprietary models)
- Models shall be stored in `%APPDATA%/local-whisper/models/`
- Models shall NOT be automatically downloaded on first run or application start
- The main window shall display the currently selected model name and size (or "No model selected" if none)
- The main window shall have a "Models" button that opens a dedicated model selection screen
- The model selection screen shall display all available models as a list with:
  - Model name and size
  - Short description of the model (e.g., "Best accuracy", "Fastest")
  - Download status: "Downloaded" label (green) for downloaded models, "Download" button for not-downloaded models
  - Radio button selection to choose which model to use
- Each not-downloaded model shall have its own "Download" button to start downloading
- When a download is in progress, all other download buttons shall be disabled (only one download at a time)
- Download progress shall be displayed within the model card being downloaded
- The "Use this model" button shall only be enabled when a downloaded model is selected
- The currently selected model shall be used for all transcription tasks
- The selected model preference shall persist across application sessions

### FR-8: Download Progress Tracking
- Download progress shall be tracked and displayed by bytes downloaded, not by file count
- The progress bar shall show accurate percentage based on total bytes downloaded vs. total bytes to download
- Progress messages shall display the current file being downloaded along with downloaded/total bytes (e.g., "Downloading model.bin (1.2 GB/1.5 GB)")
- Progress updates shall be displayed in real-time during the download process
- Download progress shall be displayed in the model selection screen (within the model card being downloaded)
- Download progress and model loading shall be separate phases:
  - Download phase: Progress bar shows 0-100% based on bytes downloaded (in model selection screen)
  - Loading phase: After model is selected, main window shows "Loading {model} into memory..." with indeterminate progress
- The progress bar shall update smoothly during large file downloads, not just between files

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
| STT Model | faster-whisper (tiny, base, small, medium, large-v3) | Speech recognition |
| Model Download | huggingface_hub | Download models from HuggingFace Hub |
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

