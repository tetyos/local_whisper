# Local Whisper - Technical Documentation

## Project Structure

```
local_whisper/
├── src/
│   └── local_whisper/
│       ├── __init__.py           # Package initialization with version info
│       ├── main.py               # Application entry point
│       ├── app.py                # Main application controller (state machine)
│       ├── audio_recorder.py     # Microphone audio capture module
│       ├── transcriber.py        # Whisper model integration for STT
│       ├── hotkey_handler.py     # Global Ctrl+Space hotkey listener
│       ├── text_output.py           # Text typing into active window
│       └── ui/
│           ├── __init__.py       # UI package init
│           ├── main_window.py    # PyQt6 main window UI
│           └── system_tray.py    # System tray icon and menu
├── assets/
│   └── create_icon.py            # Script to generate application icon
├── requirements.txt              # Python package dependencies
├── requirements.md               # Full functional requirements specification
├── build.spec                    # PyInstaller configuration for .exe build
├── build.bat                     # Windows batch script to build executable
├── run_dev.bat                   # Windows batch script for development mode
├── README.md                     # User-facing documentation
├── tech.md                       # This file - technical documentation
└── .gitignore                    # Git ignore patterns
```

## How to Run

### Development Mode

1. **Run the development script:**
   ```bash
   run_dev.bat
   ```

2. **What it does:**
   - Creates a Python virtual environment (if it doesn't exist)
   - Installs all dependencies from `requirements.txt`
   - Launches the application in development mode
   - Press `Ctrl+C` to stop

3. **First run:**
   - The Whisper base model (~150MB) will be downloaded automatically
   - Model is stored in `%APPDATA%\local-whisper\models\`
   - This may take a few minutes depending on your internet connection

### Building the Installer (.exe)

1. **Run the build script:**
   ```bash
   build.bat
   ```

2. **What it does:**
   - Creates/activates virtual environment
   - Installs dependencies including PyInstaller
   - Builds a standalone Windows executable
   - Executable is created in `dist\local-whisper.exe`

3. **Distribution:**
   - The `.exe` file is self-contained (no Python installation required)
   - Users can run it directly without any setup
   - First run will still download the Whisper model

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.local_whisper.main

# Or build the executable
pyinstaller build.spec
```

## Dependencies

### Core Dependencies

#### `faster-whisper>=1.0.0`
**Purpose:** Speech-to-text model inference engine  
**Why:** Provides optimized Whisper model implementation using CTranslate2, offering 4x faster inference than the original OpenAI Whisper while maintaining the same accuracy. It handles model loading, audio transcription, and language detection. The base model (~150MB) provides a good balance between speed and accuracy for real-time transcription.

**Used in:** `transcriber.py`

#### `sounddevice>=0.4.6`
**Purpose:** Audio input/output library  
**Why:** Cross-platform library for recording audio from microphones. Provides low-latency access to audio devices with a simple callback-based API. Works seamlessly with NumPy arrays, which is perfect for feeding audio data directly to the Whisper model.

**Used in:** `audio_recorder.py`

#### `numpy>=1.24.0`
**Purpose:** Numerical computing library  
**Why:** Required for audio data manipulation (storing recorded audio as float32 arrays), array operations, and as a dependency for sounddevice and faster-whisper. NumPy arrays are the standard format for audio processing in Python.

**Used in:** `audio_recorder.py`, `transcriber.py`

#### `keyboard>=0.13.5`
**Purpose:** Global hotkey detection library  
**Why:** Enables system-wide hotkey registration that works even when the application is not in focus. This is essential for the Ctrl+Space functionality to work from any application. The library hooks into low-level keyboard events on Windows.

**Used in:** `hotkey_handler.py`

#### `pyautogui>=0.9.54`
**Purpose:** GUI automation library  
**Why:** Simulates keyboard input to type transcribed text into the currently active window. Uses Windows API to send keystrokes programmatically, allowing the app to insert text into any application (text editors, browsers, etc.) as if the user typed it manually.

**Used in:** `text_output.py`

#### `PyQt6>=6.5.0`
**Purpose:** Cross-platform GUI framework  
**Why:** Modern, feature-rich GUI toolkit for creating the application window and system tray icon. Provides native-looking Windows UI components, system tray integration, and excellent threading support for background operations (model loading, transcription). PyQt6 is the latest version with better performance and modern APIs.

**Used in:** `main.py`, `ui/main_window.py`, `ui/system_tray.py`

#### `pyinstaller>=6.0.0`
**Purpose:** Application packaging tool  
**Why:** Bundles the Python application and all dependencies into a single Windows executable (.exe file). This allows distribution without requiring users to install Python or any dependencies. Handles complex dependency resolution and creates a standalone installer.

**Used in:** Build process (`build.spec`, `build.bat`)

### Optional Dependencies

#### `Pillow` (for icon generation)
**Purpose:** Image processing library  
**Why:** Used by `assets/create_icon.py` to generate the application icon programmatically. Not required for the main application to run, but useful for creating custom icons.

**Used in:** `assets/create_icon.py`

## Architecture Overview

### Component Flow

```
User presses Ctrl+Space
    ↓
HotkeyHandler detects event
    ↓
App controller starts AudioRecorder
    ↓
AudioRecorder captures microphone input
    ↓
User presses Ctrl+Space again
    ↓
AudioRecorder stops, returns audio data
    ↓
Transcriber processes audio with Whisper model
    ↓
TextOutput types transcribed text into active window
    ↓
App returns to idle state
```

### State Machine

The application uses a state machine pattern with the following states:
- **LOADING**: Initial model download and setup
- **IDLE**: Ready to record
- **RECORDING**: Actively capturing audio
- **TRANSCRIBING**: Processing audio with Whisper (shows ETA)
- **TYPING**: Inserting text into active window
- **DOWNLOADING**: Downloading a model
- **NO_MODEL**: No model selected/downloaded
- **ERROR**: Error state with recovery

### Transcription Time Estimation

The application provides estimated remaining time during transcription:

1. **Historical Data**: Transcription times are stored per model in `%APPDATA%/local-whisper/transcription_stats.json`
2. **Estimation Algorithm**:
   - Calculates average ratio: transcription_time / audio_duration
   - Uses historical data if available (last 20 samples per model)
   - Falls back to default estimates based on model size:
     - tiny: 0.3x (30% of audio duration)
     - base: 0.5x
     - small: 1.0x (real-time)
     - medium: 2.5x
     - large-v3: 5.0x
3. **Progress Tracking**: Uses segment timestamps from faster-whisper to track progress during transcription
4. **UI Display**: Shows progress bar with percentage, elapsed time, and estimated remaining time

### Threading Model

- **Main Thread**: PyQt6 event loop (UI updates)
- **Background Threads**: 
  - Model loading (first run)
  - Audio transcription (to avoid blocking UI)
  - Hotkey callbacks (to prevent blocking)

## Technical Decisions

### Why faster-whisper over OpenAI Whisper?
- 4x faster inference speed
- Lower memory footprint
- Better CPU performance (important for users without GPU)
- Same accuracy and model compatibility

### Why PyQt6 over Tkinter?
- Better system tray integration
- More modern and customizable UI
- Better threading support
- Native look and feel on Windows

### Why sounddevice over pyaudio?
- Simpler API
- Better NumPy integration
- More active maintenance
- Cross-platform consistency

### Why keyboard library?
- System-wide hotkey support (works when app not focused)
- Simple API for global hotkeys
- Windows-specific optimizations
- No need for complex Windows API calls

### Windowed Application Behavior
When built as a windowed application (PyInstaller `console=False`), `sys.stdout` and `sys.stderr` are set to `None` by the runtime.
To prevent crashes in libraries that attempt to write to these streams (e.g., `tqdm`, `print` calls), the application redirects them to `os.devnull` at startup in `src/local_whisper/main.py`. This ensures stability even if libraries try to log output.

## Data Storage

- **Settings**: `%APPDATA%/local-whisper/settings.json` - User preferences (selected model)
- **Transcription Stats**: `%APPDATA%/local-whisper/transcription_stats.json` - Historical transcription times for ETA estimation
- **Models**: `%APPDATA%/local-whisper/models/` - Downloaded Whisper models (HuggingFace cache format)

## File Size Considerations

- **Base executable**: ~50-100MB (includes Python runtime and dependencies)
- **Whisper base model**: ~150MB (downloaded on first run)
- **Total disk space**: ~250MB after first run

## Performance Notes

- **Model loading**: ~2-5 seconds on first run
- **Recording latency**: <200ms
- **Transcription speed**: ~2-3x real-time (10 seconds of audio = ~3-5 seconds to transcribe)
- **Typing speed**: Configurable (default 0.005s per character)

## Platform Support

- **Primary**: Windows 10/11
- **Python**: 3.11+ (for development)
- **Architecture**: x64 (64-bit)