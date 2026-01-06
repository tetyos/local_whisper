# Local Whisper

A simple speech-to-text application for Windows powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper), an optimized version of OpenAI's Whisper model.

## Features

- **Global Hotkey**: Press `Ctrl+Space` to start/stop recording
- **Direct Text Input**: Transcribed text is typed directly into the active window
- **System Tray**: Runs quietly in the system tray
- **Offline**: Works completely offline after initial model download
- **Open Source**: Uses Whisper (MIT License) - free for commercial use

## Installation

### From Release (Recommended)

1. Download the latest `local-whisper.exe` from Releases
2. Run the installer
3. Launch "local-whisper" from the Start Menu

### From Source

For development, you can use the provided helper script:

```bash
# Clone the repository
git clone https://github.com/yourusername/local-whisper.git
cd local-whisper

# Run the development script (handles venv setup and dependencies)
run_dev.bat
```

Or setup manually:

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.local_whisper.main
```

## Usage

1. Launch the application
2. On first run, you will need to select and download a model (the base model is ~150MB)
3. Press `Ctrl+Space` to start recording
4. Speak your text
5. Press `Ctrl+Space` again to stop and transcribe
6. The text will be typed into your active application

## Building the Installer

```bash
# Install PyInstaller
pip install pyinstaller

# Build the .exe
pyinstaller build.spec
```

The executable will be in the `dist` folder.

## Requirements

- Windows 10 or 11
- Microphone
- ~500MB disk space (for model and application)

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Optimized Whisper implementation

