# WhisperBurn

**WhisperBurn** is an AI-powered local subtitle generator and burner. It uses **WhisperX** for highly accurate, word-level timed subtitles and **FFmpeg** to burn them directly into videos with custom styling.

> **Status**: Prototype (v1). A native desktop version is in development.

## 🚀 Features

- **🎯 Word-Level Precision**: Uses [WhisperX](https://github.com/m-bain/whisperx) to generate subtitles with exact word-level timing (forced alignment).
- **🎨 Visual Editor**: Edit subtitle text and customize styles (Colors, Fonts, Borders, Margins) before burning.
- **✂️ Video Trimming**: Built-in simple video trimmer to process only the clips you need.
- **🔥 One-Click Burn**: Automatically embeds subtitles into the video using FFmpeg.
- **🔒 Fully Local**: Runs entirely on your machine. No data is uploaded to the cloud.
- **🚀 Zero-Config Launcher**: Automatically manages a virtual environment and installs not only Python dependencies but also specific CUDA-enabled PyTorch versions.

## 🛠️ Prerequisites

To run WhisperBurn effectively, you need:

- **OS**: Windows 10/11
- **GPU**: NVIDIA GPU (Required for WhisperX fast alignment and performance).
  - *Note: CPU mode is available but significantly slower and not recommended.*
- **FFmpeg**: Must be installed and added to your system `PATH`. [Download FFmpeg here](https://ffmpeg.org/download.html).

## 📥 Installation & Usage

WhisperBurn comes with a self-contained launcher that handles setup.

1.  **Clone or Download** this repository.
2.  **Run the Launcher**:
    Double-click `launcher.py` or run it from a terminal:
    ```bash
    python launcher.py
    ```
    *The launcher will automatically:*
    - Create a local virtual environment (`venv_wb`).
    - Install PyTorch (CUDA 12.1), WhisperX, and other dependencies.
    - Launch the Web UI.

## 📖 How to Use

Once the UI opens in your browser (usually `http://127.0.0.1:7860`):

### Step 1: Transcribe
1.  **Select Model**: Choose a Whisper model size (e.g., `medium`, `large-v2`).
2.  **Input Video**: Upload your video file.
3.  **Trim (Optional)**: Set Start and End times if you only want to process a clip.
4.  **Sync Offset**: Adjust if audio/video sync is slightly off.
5.  Click **"Step 1: Generate Subtitles"**.
    - *This will generate an `.ass` subtitle file and a preview.*

### Step 2: Edit & Style
1.  **Editor**: Review the generated subtitles in the text editor. You can fix typos or adjust timings manually if needed.
2.  **Styling**:
    - **Pick Colors**: Text and Border colors (Yellow, White, Black, Orange, etc.).
    - **Font Size & Borders**: Adjust sliders to change size and outline thickness.
    - **Margin**: Adjust vertical position.
3.  Click **"Step 2: Burn Video"**.
    - *The final video will be rendered to the `output_videos` folder.*

## 📂 Output

All processed files are saved in the `output_videos/` directory:
- `*_trim.mp4`: The trimmed segment.
- `*.ass`: The raw subtitle file.
- `*_final.mp4`: The final video with burned-in subtitles.

## ⚠️ Troubleshooting

- **"FFmpeg not found"**: Make sure FFmpeg is installed and `ffmpeg` works in your terminal.
- **"CUDA/GPU errors"**: Ensure you have up-to-date NVIDIA drivers. The launcher installs PyTorch with CUDA 12.1 support.
- **Slow Performance**: Large models (`large-v2`) require more VRAM (~8GB). Try `medium` or `small` if you run out of memory.

## 📜 License

[MIT License](LICENSE)
