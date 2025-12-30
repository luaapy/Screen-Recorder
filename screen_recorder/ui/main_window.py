import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys
import subprocess
import platform
import webbrowser

# Ensure local package is found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.config import load_config, save_config
from recorder.audio_capture import AudioRecorder

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self, start_callback=None, stop_callback=None, pause_callback=None, resume_callback=None, config=None):
        super().__init__()
        
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        self.config = config if config else {}
        
        self.title("Screen Recorder Pro")
        self.geometry("600x600") # Increased height for audio list
        self.resizable(True, True)
        # Use default dark mode colors (don't override with white)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#4A90E2")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.title_label = ctk.CTkLabel(self.header_frame, text="Screen Recorder Pro", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
        self.title_label.pack(pady=10, padx=20, side="left")

        # Tab View
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.tab_general = self.tab_view.add("General")
        self.tab_video = self.tab_view.add("Video")
        self.tab_audio = self.tab_view.add("Audio")
        
        self._setup_general_tab()
        self._setup_video_tab()
        self._setup_audio_tab()

        # Status & Controls
        self.control_frame = ctk.CTkFrame(self, height=120, fg_color="transparent")
        self.control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.timer_label = ctk.CTkLabel(self.control_frame, text="00:00:00", font=ctk.CTkFont(size=36, weight="bold"), text_color="white")
        self.timer_label.pack(pady=5)
        
        self.status_label = ctk.CTkLabel(self.control_frame, text="Status: Ready", text_color="gray")
        self.status_label.pack(pady=(0, 10))
        
        self.buttons_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.buttons_frame.pack()
        
        self.btn_start = ctk.CTkButton(self.buttons_frame, text="START RECORDING", command=self.on_start, 
                                       fg_color="#28A745", hover_color="#218838", width=180, height=40, font=ctk.CTkFont(weight="bold"))
        self.btn_start.grid(row=0, column=0, padx=10)
        
        self.btn_pause = ctk.CTkButton(self.buttons_frame, text="PAUSE", command=self.on_pause, 
                                       fg_color="#6C757D", hover_color="#5A6268", width=100, height=40, state="disabled")
        self.btn_pause.grid(row=0, column=1, padx=10)
        
        self.btn_stop = ctk.CTkButton(self.buttons_frame, text="STOP", command=self.on_stop, 
                                      fg_color="#DC3545", hover_color="#C82333", width=100, height=40, state="disabled")
        self.btn_stop.grid(row=0, column=2, padx=10)
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.btn_open_folder = ctk.CTkButton(self.footer_frame, text="Open Folder", command=self.open_output_folder, fg_color="#4A90E2", width=120)
        self.btn_open_folder.pack(side="right")

    def _setup_general_tab(self):
        # Mode
        self.mode_frame = ctk.CTkFrame(self.tab_general)
        self.mode_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(self.mode_frame, text="Recording Mode:", font=ctk.CTkFont(weight="bold"), text_color="white").pack(anchor="w", padx=10, pady=5)
        self.record_mode = ctk.StringVar(value="Full Screen")
        ctk.CTkRadioButton(self.mode_frame, text="Full Screen", variable=self.record_mode, value="Full Screen", text_color="white").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(self.mode_frame, text="Select Region", variable=self.record_mode, value="Select Region", text_color="white").pack(anchor="w", padx=20, pady=2)

        # Output
        self.output_frame = ctk.CTkFrame(self.tab_general)
        self.output_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(self.output_frame, text="Output Folder:", font=ctk.CTkFont(weight="bold"), text_color="white").pack(anchor="w", padx=10, pady=5)
        self.path_entry = ctk.CTkEntry(self.output_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.path_entry.insert(0, self.config.get("save_path", ""))
        ctk.CTkButton(self.output_frame, text="Browse...", width=80, command=self.browse_folder).pack(side="right", padx=(0, 10), pady=10)

        # Options
        self.chk_cursor = ctk.CTkCheckBox(self.tab_general, text="Show Cursor", onvalue=True, offvalue=False, text_color="white")
        self.chk_cursor.pack(anchor="w", padx=10, pady=5)
        if self.config.get("show_cursor"): self.chk_cursor.select()

        self.chk_countdown = ctk.CTkCheckBox(self.tab_general, text="Show Countdown (3s)", onvalue=True, offvalue=False, text_color="white")
        self.chk_countdown.pack(anchor="w", padx=10, pady=5)
        if self.config.get("show_countdown"): self.chk_countdown.select()

    def _setup_video_tab(self):
        ctk.CTkLabel(self.tab_video, text="FPS:", text_color="white").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.fps_option = ctk.CTkOptionMenu(self.tab_video, values=["15", "20", "30", "60"])
        self.fps_option.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        self.fps_option.set(str(self.config.get("fps", "30")))
        
        ctk.CTkLabel(self.tab_video, text="Codec:", text_color="white").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.codec_option = ctk.CTkOptionMenu(self.tab_video, values=["MP4V", "XVID"])
        self.codec_option.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        self.codec_option.set(self.config.get("codec", "MP4V"))

    def _setup_audio_tab(self):
        # Audio Source Type
        ctk.CTkLabel(self.tab_audio, text="Audio Source Mode:", font=ctk.CTkFont(weight="bold"), text_color="white").pack(anchor="w", padx=10, pady=(10, 5))
        self.audio_source_type = ctk.CTkOptionMenu(self.tab_audio, 
                                                   values=["Microphone", "System Audio", "Both", "None"],
                                                   command=self.on_audio_source_change)
        self.audio_source_type.pack(anchor="w", padx=10, pady=5)
        self.audio_source_type.set(self.config.get("audio_source", "Microphone"))
        
        # Microphone Device Selection
        ctk.CTkLabel(self.tab_audio, text="Microphone Device:", text_color="white").pack(anchor="w", padx=10, pady=(10, 5))
        self.mic_device_option = ctk.CTkOptionMenu(self.tab_audio, values=["Default"])
        self.mic_device_option.pack(anchor="w", padx=10, pady=5)
        
        # System Device Selection (For loopback)
        ctk.CTkLabel(self.tab_audio, text="System Device (Loopback):", text_color="white").pack(anchor="w", padx=10, pady=(10, 5))
        self.sys_device_option = ctk.CTkOptionMenu(self.tab_audio, values=["Default"])
        self.sys_device_option.pack(anchor="w", padx=10, pady=5)
        
        # Populate Devices
        self.populate_audio_devices()
        self.on_audio_source_change(self.audio_source_type.get())

    def populate_audio_devices(self):
        # Get devices from AudioRecorder
        input_devices = AudioRecorder.get_devices(kind='input')
        
        # Format for display: "Index: Name (HostAPI)"
        self.mic_device_names = [f"{d['index']}: {d['name']}" for d in input_devices]
        if not self.mic_device_names:
            self.mic_device_names = ["No Input Devices Found"]
            
        self.mic_device_option.configure(values=self.mic_device_names)
        if self.mic_device_names:
            self.mic_device_option.set(self.mic_device_names[0])
            
        # For System audio, on Windows, we usually look for Loopback devices. 
        # Since we can't easily filter 'loopback' without checking the name or specific hostapi flags which sd might not expose easily without stream init,
        # we list all output devices or look for WASAPI.
        # For simplicity, we list all devices and let user choose the one that says "Loopback" or "Stereo Mix" if available,
        # OR we just list all devices.
        # Actually, sounddevice query_devices returns everything.
        all_devices = AudioRecorder.get_devices()
        self.sys_device_names = [f"{d['index']}: {d['name']}" for d in all_devices if d['max_input_channels'] > 0 or 'Loopback' in d['name']]
        # Ideally we want WASAPI loopback, which appears as input in some contexts or needs special init.
        
        if not self.sys_device_names:
             self.sys_device_names = ["Default System Audio"]
             
        self.sys_device_option.configure(values=self.sys_device_names)
        if self.sys_device_names:
            self.sys_device_option.set(self.sys_device_names[0])

    def on_audio_source_change(self, choice):
        # Enable/Disable dropdowns based on mode
        if choice == "Microphone":
            self.mic_device_option.configure(state="normal")
            self.sys_device_option.configure(state="disabled")
        elif choice == "System Audio":
            self.mic_device_option.configure(state="disabled")
            self.sys_device_option.configure(state="normal")
        elif choice == "Both":
            self.mic_device_option.configure(state="normal")
            self.sys_device_option.configure(state="normal")
        else: # None
            self.mic_device_option.configure(state="disabled")
            self.sys_device_option.configure(state="disabled")

    def get_selected_audio_indices(self):
        mic_idx = None
        sys_idx = None
        
        try:
            mic_val = self.mic_device_option.get()
            if ":" in mic_val:
                mic_idx = int(mic_val.split(":")[0])
                
            sys_val = self.sys_device_option.get()
            if ":" in sys_val:
                sys_idx = int(sys_val.split(":")[0])
        except:
            pass
            
        return mic_idx, sys_idx

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.config["save_path"] = folder
            save_config(self.config)

    def open_output_folder(self):
        path = self.path_entry.get()
        if os.path.exists(path):
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", path])
        else:
            messagebox.showerror("Error", "Folder does not exist!")

    def on_start(self):
        self.update_config_from_ui()
        if self.start_callback:
            self.start_callback()
        
    def on_stop(self):
        if self.stop_callback:
            self.stop_callback()

    def on_pause(self):
        if self.btn_pause.cget("text") == "PAUSE":
            if self.pause_callback:
                self.pause_callback()
            self.btn_pause.configure(text="RESUME")
            self.status_label.configure(text="Status: Paused")
        else:
            if self.resume_callback:
                self.resume_callback()
            self.btn_pause.configure(text="PAUSE")
            self.status_label.configure(text="Status: Recording")

    def update_config_from_ui(self):
        self.config["save_path"] = self.path_entry.get()
        self.config["fps"] = int(self.fps_option.get())
        self.config["codec"] = self.codec_option.get()
        self.config["show_cursor"] = bool(self.chk_cursor.get())
        self.config["show_countdown"] = bool(self.chk_countdown.get())
        self.config["audio_source"] = self.audio_source_type.get()
        # Note: We don't save device indices persistently as IDs might change between reboots/unplugs
        save_config(self.config)

    def set_recording_state(self, is_recording):
        if is_recording:
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.btn_pause.configure(state="normal")
            self.status_label.configure(text="Status: Recording", text_color="red")
            self.tab_view.configure(state="disabled")
        else:
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.btn_pause.configure(state="disabled", text="PAUSE")
            self.status_label.configure(text="Status: Ready", text_color="gray")
            self.tab_view.configure(state="normal")

    def set_processing_state(self):
        self.status_label.configure(text="Status: Processing...", text_color="orange")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")

    def update_timer(self, time_str):
        self.timer_label.configure(text=time_str)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
