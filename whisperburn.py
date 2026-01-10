import sys
import os
import datetime

# --- DEBUG LOGGING SETUP ---
log_file = open("debug_log.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file
print(f"=== WhisperBurn Log Started at {datetime.datetime.now()} ===")
# ---------------------------

import gradio as gr
import whisperx
import subprocess
import torch
import shutil
import gc
import re
from pathlib import Path


# VISUAL THEME (Dark + Orange)
###################################
theme = gr.themes.Soft(
    primary_hue="orange",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"],
).set(
    body_background_fill="#0b0f19",  # Deep black/blue background
    block_background_fill="#111827",  # Slightly lighter blocks
    block_border_width="1px",
    block_border_color="#374151", # Subtle borders
    button_primary_background_fill="#f97316", # Bright Orange
    button_primary_background_fill_hover="#ea580c",
    button_primary_text_color="white",
    slider_color="#f97316",
    input_background_fill="#1f2937",
    input_border_color="#374151"
)

# Custom CSS
css = """
.gradio-container { background-color: #0b0f19 !important; }

/* FIX: Remove ugly orange background from labels */
label span { background-color: transparent !important; color: #f97316 !important; font-weight: bold; }
span.svelte-1gfkn6j { background-color: transparent !important; color: #f97316 !important; }

/* Header Styling */
h1 { color: #f97316 !important; font-weight: 800 !important; font-size: 2.5rem !important; text-align: center; }
.pro-badge { background: #f97316; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; vertical-align: middle; }

/* Hide the footer */
footer { display: none !important; }
"""

# APP LOGIC
###################
OUTPUT_DIR = "./output_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLOR_MAP = {
    "White": "&H00FFFFFF", "Black": "&H00000000", "Yellow": "&H0000FFFF",
    "Cyan": "&H00FFFF00", "Lime": "&H0000FF00", "Magenta": "&H00FF00FF",
    "Orange": "&H0000AAFF", "Red": "&H000000FF", "Blue": "&H00FF0000"
}

def get_gpu_info():
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        return f"GPU Active: {torch.cuda.get_device_name(0)} ({vram:.1f} GB VRAM)"
    return "Running on CPU (Slow)"

def load_model_smart(model_name, device_pref):
    device = "cuda" if torch.cuda.is_available() and device_pref != "CPU" else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    clean_name = model_name.split(" ")[0].lower()
    
    print(f"Loading {clean_name} on {device} ({compute_type})...")
    try:
        model = whisperx.load_model(clean_name, device, compute_type=compute_type)
        return model, device, compute_type
    except ValueError as e:
        if "float16" in str(e) and device == "cuda":
            print("GPU float16 not supported/OOM. Retrying with int8...")
            gc.collect(); torch.cuda.empty_cache()
            return whisperx.load_model(clean_name, device, compute_type="int8"), device, "int8"
        raise e
    except Exception as e:
        if "out of memory" in str(e).lower() and device == "cuda":
             print("GPU OOM. Retrying with int8...")
             gc.collect(); torch.cuda.empty_cache()
             return whisperx.load_model(clean_name, device, compute_type="int8"), device, "int8"
        raise e

def to_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def generate_ass_content(segments, font_size=48, text_color="&H0000FFFF", 
                         border_color="&H00000000", border_width=2, 
                         margin_bottom=80, margin_side=40):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{text_color},&H000000FF,{border_color},&H00000000,0,0,0,0,100,100,0,0,1,{border_width},0,2,{margin_side},{margin_side},{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = ""
    events += "; =======================================\n"
    events += ";    EDIT SUBTITLES BELOW THIS LINE      \n"
    events += "; =======================================\n"
    for seg in segments:
        start = to_ass_time(seg['start'])
        end = to_ass_time(seg['end'])
        text = seg['text'].strip().replace('\n', ' ').replace('\r', '')
        events += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"
    return header + events

# STEP 1: GENERATE 
def step1_transcribe(video, start, end, model, offset, device_pref, progress=gr.Progress()):
    if not video: return None, None, None
    name = Path(video).stem.replace(" ", "_")[:30]
    trim = f"{OUTPUT_DIR}/{name}_trim.mp4"
    
    progress(0.1, desc="Trimming Video...")
    subprocess.run(["ffmpeg", "-y", "-ss", start, "-i", video, "-to", end, "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", trim], capture_output=True, check=True)
    
    progress(0.3, desc="Loading AI Model...")
    model_obj, device, dtype = load_model_smart(model, device_pref)
    
    progress(0.5, desc="Transcribing...")
    audio = whisperx.load_audio(trim)
    result = model_obj.transcribe(audio, batch_size=16)
    
    progress(0.7, desc="Aligning Timestamps...")
    align_model, metadata = whisperx.load_align_model(result["language"], device)
    result = whisperx.align(result["segments"], align_model, metadata, audio, device)
    segs = result["segments"]
    
    for seg in segs:
        seg['start'] += offset
        seg['end'] += offset

    ass_content = generate_ass_content(segs)
    ass_file = f"{OUTPUT_DIR}/{name}.ass"
    with open(ass_file, "w", encoding="utf-8") as f: f.write(ass_content)

    del model_obj, align_model
    gc.collect(); torch.cuda.empty_cache()
    return trim, ass_content, ass_file

# STEP 2: BURN 
def step2_burn(trimmed_video, ass_content, text_col, bor_col, fs, bw, margin, progress=gr.Progress()):
    if not trimmed_video or not ass_content: return None
    progress(0.1, desc="Rendering Subtitles...")
    name = Path(trimmed_video).stem
    final = f"{OUTPUT_DIR}/{name}_final.mp4"
    temp_ass = f"{OUTPUT_DIR}/{name}_temp_edit.ass"
    
    t_color = COLOR_MAP.get(text_col, "&H0000FFFF")
    b_color = COLOR_MAP.get(bor_col, "&H00000000")
    new_style = (f"Style: Default,Arial,{fs},{t_color},&H000000FF,{b_color},"
                 f"&H00000000,0,0,0,0,100,100,0,0,1,{bw},0,2,40,40,{margin},1")
    updated_content = re.sub(r"Style: Default.*", new_style, ass_content)
    with open(temp_ass, "w", encoding="utf-8") as f: f.write(updated_content)
    
    progress(0.5, desc="Burning Video (FFmpeg)...")
    safe_ass_path = os.path.abspath(temp_ass).replace("\\", "/").replace(":", "\\:")
    subprocess.run(["ffmpeg", "-y", "-i", trimmed_video, "-vf", f"subtitles='{safe_ass_path}'", "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", final], capture_output=True, check=True)
    return final


# UI LAYOUT
################
with gr.Blocks(title="WhisperBurn", theme=theme, css=css) as demo:
    with gr.Row():
        gr.Markdown("# WhisperBurn <span class='pro-badge'>AI</span>")
    
    gr.Markdown(f"**Status**: {get_gpu_info()}")
    
    with gr.Row():
        # LEFT COLUMN (Controls)
        with gr.Column(scale=4):
            gr.Markdown("### 1. Settings & Input")
            md = gr.Dropdown(
                ["tiny (~1GB)", "base (~1GB)", "small (~2GB)", "medium (~5GB)", "large-v2 (~8GB)"], 
                value="medium (~5GB)", label="AI Model"
            )
            dev = gr.Radio(["Auto", "CPU"], value="Auto", label="Device", interactive=True)
            
            vid = gr.Video(label="Input Video")
            
            gr.Markdown("###Trim Video")
            with gr.Row():
                st = gr.Textbox("00:00:00", label="Start")
                en = gr.Textbox("00:00:30", label="End")
            
            offset = gr.Slider(-2.0, 2.0, value=0.0, step=0.1, label="Sync Offset (s)")
            btn_gen = gr.Button("Step 1: Generate Subtitles", variant="primary", size="lg")

        # RIGHT COLUMN (Editor & Output)
        with gr.Column(scale=5):
            gr.Markdown("### 2. Review & Style")
            ass_editor = gr.Code(label="Subtitle Editor (Edit Text Here)", lines=50)
            trimmed_vid_state = gr.State()
            
            with gr.Group():
                with gr.Row():
                    txt_col = gr.Radio(list(COLOR_MAP.keys()), value="Yellow", label="Text")
                    bor_col = gr.Radio(list(COLOR_MAP.keys()), value="Black", label="Border")
                with gr.Row():
                    fs = gr.Slider(24, 100, value=60, step=2, label="Font Size")
                    bw = gr.Slider(1, 5, value=2, label="Border Width")
                    margin = gr.Slider(0, 300, value=80, step=10, label="Margin")
            
            btn_burn = gr.Button("Step 2: Burn Video", variant="stop", size="lg")
            final_vid = gr.Video(label="Final Result")
            download_ass = gr.File(label="Download Subtitles", visible=False)

    btn_gen.click(step1_transcribe, [vid, st, en, md, offset, dev], [trimmed_vid_state, ass_editor, download_ass])
    btn_burn.click(step2_burn, [trimmed_vid_state, ass_editor, txt_col, bor_col, fs, bw, margin], [final_vid])

if __name__ == "__main__":
    import multiprocessing
    import os
    import sys
    import webbrowser
    import time
    import threading

    # 1. STOP WORKER PROCESSES FROM RELOADING UI
    if os.environ.get("WHISPERBURN_WORKER") == "1":
        sys.exit(0)

    # 2. Set the flag for the next process
    os.environ["WHISPERBURN_WORKER"] = "1"
    
    # 3. Freeze support
    multiprocessing.freeze_support()

    # 4. Helper to open browser
    def open_browser():
        time.sleep(5) 
        print("Opening browser...")
        webbrowser.open("http://127.0.0.1:7860")

    # Start browser opener
    threading.Thread(target=open_browser, daemon=True).start()

    # 5. Launch
    print("Starting WhisperBurn UI...")
    demo.launch(
    server_name="127.0.0.1", 
    server_port=7860, 
    inbrowser=False, 
    show_api=False
)

