# Screen Recorder Pro for Windows 10

A modern, clean, and efficient desktop screen recorder built with Python.

## Features

- **Recording Modes**: Full Screen or Select Region (Drag-to-select).
- **Audio Recording**: Microphone, System Audio (WASAPI), or Both.
- **Video Quality**: Adjustable FPS (15-60), Quality Presets (720p, 1080p, Native), and Codecs (MP4V, XVID).
- **Modern UI**: Clean design using CustomTkinter (White/Blue/Green theme).
- **Controls**: Hotkeys (F9 Start, F10 Pause, F11 Stop), Countdown timer, Status indicators.
- **Output**: Auto-merges audio/video using FFmpeg to MP4. Saves to user-defined folder.

## Prerequisites

1. **Python 3.8+**
2. **FFmpeg**: This application requires FFmpeg to merge audio and video.
   - Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - **Important**: You must add `ffmpeg/bin` to your System PATH environment variable so that the command `ffmpeg` works in a terminal.

## Installation

1. Clone or download this repository.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the main application:

```bash
python screen_recorder/main.py
```

### Hotkeys
- **F9**: Start Recording
- **F10**: Pause/Resume Recording
- **F11**: Stop Recording

## Configuration

Settings are automatically saved to `config.json` in the application directory. You can also change them via the "Settings" tabs in the UI.

## Troubleshooting

- **"FFmpeg Missing" Error**: Ensure FFmpeg is installed and added to your System PATH. Restart your computer after adding it to PATH.
- **System Audio Not Recording**: Ensure "Stereo Mix" or similar loopback devices are enabled in Windows Sound Settings, or that the application has permission to access audio devices.
- **Region Selection Black Screen**: This might happen if you are running full-screen games. Try running games in "Windowed Borderless" mode.

## Development

Project Structure:
- `screen_recorder/main.py`: Entry point.
- `screen_recorder/ui/`: UI components.
- `screen_recorder/recorder/`: Video/Audio capture logic.
- `screen_recorder/utils/`: Configuration and helpers.
