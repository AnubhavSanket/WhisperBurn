import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk
import multiprocessing 

class SplashLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhisperBurn Launcher")
        self.root.geometry("400x250")
        self.root.configure(bg="#111827")
        self.root.overrideredirect(True) 

        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.root.geometry(f"400x250+{x}+{y}")

        # UI
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=10, troughcolor='#1f2937', background='#f97316')

        self.label_title = tk.Label(self.root, text="🔥 WhisperBurn", font=("Segoe UI", 20, "bold"), fg="#f97316", bg="#111827")
        self.label_title.pack(pady=(40, 10))

        self.label_status = tk.Label(self.root, text="Initializing...", font=("Segoe UI", 10), fg="white", bg="#111827")
        self.label_status.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="indeterminate", style="TProgressbar")
        self.progress.pack(pady=10)
        self.progress.start(15)

        # Start thread
        threading.Thread(target=self.run_process, daemon=True).start()

    def update_status(self, text):
        self.root.after(0, lambda: self.label_status.config(text=text))

    def run_process(self):
        with open("launcher_log.txt", "w", buffering=1) as f:
            def log(msg):
                f.write(msg + "\n")
                f.flush()
                print(msg)

            log("Launcher thread started.")
            
            try:
                venv_dir = os.path.join(os.getcwd(), "venv_wb")
                python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
                app_script = "whisperburn.py"

                log(f"Current Directory: {os.getcwd()}")
                
                # 1. Setup Environment
                if not os.path.exists(python_exe):
                    self.update_status("Creating virtual environment...")
                    log("Creating venv...")
                    
                    # USE CREATE_NEW_CONSOLE flags to prevent 0xc0000142 error
                    creation_flags = subprocess.CREATE_NEW_CONSOLE
                    
                    # Create venv
                    subprocess.check_call(["python", "-m", "venv", "venv_wb"], creationflags=creation_flags)
                    
                    self.update_status("Installing AI dependencies (Check popup window)...")
                    log("Installing dependencies...")
                    
                    # Install Torch (Stable 2.5.1 + CUDA 12.1)
                    # We remove the general --index-url and point to the specific wheel if needed, 
                    # but usually the standard command works better if we are specific.
                    
                    subprocess.check_call([
                        python_exe, "-m", "pip", "install", 
                        "torch==2.5.1+cu121", 
                        "torchvision==0.20.1+cu121", 
                        "torchaudio==2.5.1+cu121", 
                        "--index-url", "https://download.pytorch.org/whl/cu121"
                    ], creationflags=creation_flags)

                    # Install Other Deps
                    subprocess.check_call([
                        python_exe, "-m", "pip", "install", 
                        "git+https://github.com/m-bain/whisperx.git", 
                        "gradio==4.44.1", 
                        "gradio-client==1.3.0",  # Important
                        "omegaconf", 
                        "ffmpeg-python"
                    ], creationflags=creation_flags)

                # 2. Launch App
                if os.path.exists(app_script):
                    self.update_status("Loading AI Models... Please wait (20-40s)")
                    log(f"Found {app_script}. Launching subprocess...")
                    
                    # Launch without console window 
                    subprocess.Popen(
                        [python_exe, app_script],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    log("Subprocess launched successfully.")
                    
                    self.root.after(8000, self.root.destroy)
                else:
                    log(f"CRITICAL ERROR: {app_script} not found!")
                    self.update_status(f"Error: {app_script} missing!")
                    self.root.after(5000, self.root.destroy)

            except Exception as e:
                log(f"EXCEPTION OCCURRED: {str(e)}")
                self.update_status("Error occurred. Check logs.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = SplashLauncher()
    app.run()
