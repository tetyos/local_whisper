# Local Whisper - Technical Documentation

## Project Structure

```
local_whisper/
├── src/
│   ├── local_whisper/
│   │   ├── __init__.py           # Package initialization with version info
│   │   ├── main.py               # Application entry point
│   │   ├── app.py                # Main application controller (state machine)
│   │   ├── audio_recorder.py     # Microphone audio capture module (with audio level signal)
│   │   ├── transcriber.py        # Whisper model integration for STT
│   │   ├── hotkey_handler.py     # Global Ctrl+Space hotkey listener
│   │   ├── text_output.py        # Text typing into active window
│   │   └── ui/
│   │       ├── __init__.py             # UI package init
│   │       ├── main_window.py          # Main window coordinator
│   │       ├── main_view.py            # Main status view widget
│   │       ├── model_selector_view.py  # Model selection view widget
│   │       ├── floating_indicator.py   # Floating status indicator window
│   │       ├── styles.py               # Shared CSS styles module
│   │       └── system_tray.py          # System tray icon and menu
│   └── tests/                    # Test suite
│       ├── __init__.py
│       ├── conftest.py           # Shared pytest fixtures
│       ├── test_settings.py      # Settings unit tests
│       ├── test_transcriber.py   # Transcriber tests
│       ├── test_audio_recorder.py
│       ├── test_hotkey_handler.py
│       ├── test_text_output.py
│       ├── test_app.py           # Integration tests
│       ├── test_main_window.py   # UI tests
│       └── test_system_tray.py
├── assets/
│   └── create_icon.py            # Script to generate application icon
├── requirements.txt              # Python package dependencies
├── requirements.md               # Full functional requirements specification
├── build.spec                    # PyInstaller configuration for .exe build
├── build.bat                     # Windows batch script to build executable
├── run_dev.bat                   # Windows batch script for development mode
├── run_tests.bat                 # Windows batch script to run test suite
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
   - The application starts in "No Model" state
   - You must first select and download a model (e.g., base model ~150MB)
   - Model is stored in `%APPDATA%\local-whisper\models\`

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
   - First run will ask the user to download a model

### Automated Releases (GitHub Actions)

The project uses GitHub Actions to automatically build and release executables.

**Creating a Release:**
```bash
# Tag a commit with a version number
git tag v1.0.0
git push origin v1.0.0
```

This triggers the release workflow which:
1. Checks out the tagged source code
2. Sets up Python and installs dependencies
3. Runs the test suite
4. Builds the executable using PyInstaller
5. Generates SHA256 checksum for verification
6. Creates a GitHub Release with the executable attached

**Workflow Files:**
- `.github/workflows/release.yml` - Main build and release workflow
- `.github/dependabot.yml` - Automated dependency security updates

**Security Features:**
- Builds run on clean GitHub-hosted VMs (no local machine contamination)
- SHA256 checksums for download verification
- Dependabot monitors for vulnerable dependencies
- Full build logs are publicly auditable
- Exact source commit is linked to each release

**Pre-release Versions:**
Tags containing `-alpha`, `-beta`, or `-rc` are automatically marked as pre-releases.

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

## Testing

The project includes a comprehensive test suite to ensure functionality remains intact after refactoring or UI changes.

### Test Structure

```
src/tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── test_settings.py         # Settings module unit tests
├── test_transcriber.py      # Transcriber utility tests  
├── test_audio_recorder.py   # Audio recorder tests (mocked)
├── test_hotkey_handler.py   # Hotkey handler tests (mocked)
├── test_text_output.py      # Text output tests (mocked)
├── test_app.py              # App integration tests
├── test_main_window.py      # MainWindow UI tests
└── test_system_tray.py      # System tray UI tests
```

### Running Tests

You can run the full test suite using the provided batch script:

```bash
run_tests.bat
```

Or manually in powershell:

```bash
# Activate virtual environment
venv\Scripts\activate

# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest src/tests/

# Run with verbose output
pytest src/tests/ -v

# Run with coverage report
pytest src/tests/ --cov=src/local_whisper --cov-report=html

# Run specific test file
pytest src/tests/test_settings.py -v

# Run tests matching a pattern
pytest src/tests/ -k "test_state"
```

### Test Categories

1. **Unit Tests** - Test individual components in isolation:
   - `test_settings.py` - Settings persistence and transcription stats
   - `test_transcriber.py` - Model utilities and byte formatting
   - `test_audio_recorder.py` - Audio recording state management
   - `test_hotkey_handler.py` - Hotkey registration lifecycle
   - `test_text_output.py` - Text typing functionality

2. **Integration Tests** - Test component interactions:
   - `test_app.py` - State machine transitions, signal emissions

3. **UI Tests** - Test PyQt6 GUI components (using pytest-qt):
   - `test_main_window.py` - Main window and model selector
   - `test_system_tray.py` - System tray icon and menu

### Test Dependencies

The following packages are required for testing (included in `requirements.txt`):
- `pytest>=8.0.0` - Test framework
- `pytest-qt>=4.4.0` - PyQt6 testing support
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking utilities

### Mocking Strategy

Tests use extensive mocking to avoid hardware/external dependencies:
- **sounddevice** - Mocked to avoid microphone access
- **keyboard** - Mocked to avoid global hotkey registration
- **pyautogui** - Mocked to avoid keyboard simulation
- **faster-whisper** - Mocked to avoid loading ML models
- **huggingface_hub** - Mocked to avoid network requests

### Coverage Goals

| Component | Target | Priority |
|-----------|--------|----------|
| settings.py | 95%+ | High |
| app.py | 90%+ | High |
| main_window.py | 80%+ | High |
| transcriber.py | 90%+ | Medium |
| audio_recorder.py | 80%+ | Medium |
| hotkey_handler.py | 85%+ | Medium |
| text_output.py | 80%+ | Low |
| system_tray.py | 70%+ | Low |

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

### UI Architecture

The UI uses a modular view-based architecture for maintainability:

```
MainWindow (QMainWindow)
├── QStackedWidget (view container)
│   ├── MainView - Status display, model info, hotkey hints
│   ├── ModelSelectorView - Model list, download, selection
│   └── [Future views can be added here]
└── Coordinates navigation and state between views
```

**Key Components:**

| File | Purpose |
|------|---------|
| `main_window.py` | Window coordinator, manages `QStackedWidget`, routes signals |
| `main_view.py` | Main status view with recording state, transcription progress |
| `model_selector_view.py` | Model cards, download progress, model selection |
| `floating_indicator.py` | Always-on-top floating window for recording/transcription status |
| `styles.py` | Centralized CSS styles and color palette |
| `system_tray.py` | System tray icon and context menu |

**Adding New Views:**
1. Create a new view widget in `ui/` (e.g., `settings_view.py`)
2. Add view to `QStackedWidget` in `MainWindow._setup_ui()`
3. Add navigation signals/methods to coordinate switching
4. Import styles from `styles.py` for consistency

### Floating Status Indicator

The `FloatingIndicator` is a small always-on-top window that appears during recording and transcription:

```
Recording Mode (~170x80px):
┌─────────────────────────┐
│    🎤 Recording...      │
│  ▌▐ ▌▐▐ ▐▌▐ ▌▐          │ ← Animated audio level bars
└─────────────────────────┘

Transcribing Mode (~170x90px):
┌─────────────────────────┐
│    Transcribing...      │
│  ▓▓▓▓▓▓▓▓▓░░░░░  65%   │
│    ETA: 3s              │
└─────────────────────────┘
```

**Key Features:**
- Uses `Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus` to stay visible without stealing keyboard focus
- Frameless, semi-transparent, dark-themed to match application aesthetics
- Draggable anywhere on the window
- Default position: bottom-right corner of primary screen

**Audio Level Visualization:**
- `AudioRecorder` calculates RMS (Root Mean Square) of audio chunks and emits `audio_level_changed(float)` signal every ~50ms
- `AudioLevelWidget` displays 7 animated vertical bars that react to the audio level
- Each bar has slight random variation for a more dynamic appearance
- Smooth animation using incremental interpolation (30fps update rate)

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
- **LOADING**: Loading model into memory
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
- **Whisper base model**: ~150MB (downloaded manually)
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