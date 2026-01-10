# WhisperBurn (Prototype)

**WhisperBurn** is an AI-powered subtitle generator that creates dynamic, karaoke-style subtitles for videos. It leverages **m-bain's WhisperX** for forced alignment and word-level timing, building upon OpenAI's Whisper models.

> **Note:** This is the **v1 Prototype** (Web UI wrapper). A full native desktop application (v2) is currently in development.

## Features
- **Auto-Transcribe:** Uses `WhisperX` for word-level timestamp accuracy.
- **Karaoke Styling:** Generates `.ass` subtitle files with professional styling.
- **Video Burning:** Automatically burns subtitles into the video using FFmpeg.
- **GPU Acceleration:** Optimized for CUDA (NVIDIA GPUs).
- **Self-Contained Launcher:** Automatically handles virtual environments and dependency installation.

## Installation & Usage
1. **Prerequisites:** 
   - Windows 10/11
   - NVIDIA GPU (Recommended)
   - [FFmpeg](https://ffmpeg.org/download.html) installed and added to Path.

2. **Run the App:**
   Simply run the launcher script:
   ```bash
   python launcher.py
