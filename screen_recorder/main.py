import customtkinter as ctk
import threading
import time
import os
import datetime
import shutil
import tkinter as tk
from tkinter import messagebox
import sys
import pystray
from PIL import Image, ImageDraw

# Import components
from screen_recorder.ui.main_window import MainWindow
from screen_recorder.ui.region_selection import RegionSelectionWindow
from screen_recorder.recorder.video_capture import VideoRecorder
from screen_recorder.recorder.audio_capture import AudioRecorder
from screen_recorder.recorder.merger import merge_audio_video, get_temp_dir, cleanup_temp_files, check_ffmpeg
from screen_recorder.utils.config import load_config, save_config

try:
    import keyboard
except ImportError:
    keyboard = None

class ScreenRecorderApp:
    def __init__(self):
        self.config = load_config()
        self.window = MainWindow(
            start_callback=self.start_recording,
            stop_callback=self.stop_recording,
            pause_callback=self.pause_recording,
            resume_callback=self.resume_recording,
            config=self.config
        )
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.video_recorder = None
        self.audio_recorder = None
        
        self.is_recording = False
        self.is_paused = False
        self.recording_start_time = 0
        self.total_pause_duration = 0
        self.pause_start_time = 0
        
        self.timer_thread = None
        self.stop_event = threading.Event()
        
        self.temp_dir = get_temp_dir()
        self.temp_video_path = os.path.join(self.temp_dir, "temp_video.avi")
        self.temp_audio_path = os.path.join(self.temp_dir, "temp_audio.wav")
        
        self.tray_icon = None
        self._setup_tray()
        self.setup_hotkeys()
        
    def _setup_tray(self):
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color=(74, 144, 226))
            d = ImageDraw.Draw(image)
            d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
            
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Start Recording", self.start_recording),
                pystray.MenuItem("Stop Recording", self.stop_recording),
                pystray.MenuItem("Exit", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("ScreenRecorderPro", image, "Screen Recorder Pro", menu)
        except Exception as e:
            print(f"Tray setup failed: {e}")
            self.tray_icon = None

    def show_window(self, icon=None, item=None):
        self.window.deiconify()
        self.window.lift()

    def hide_window(self):
        self.window.withdraw()
        if self.tray_icon:
            # Run tray in separate thread to not block main loop if needed, 
            # but usually run_detached or just having it ready is enough. 
            # pystray run() is blocking, so we need a thread if we want it to persist while app runs.
            # However, if we just want the icon to exist, we might need to handle the loop carefully.
            # Best practice: Run tray in a thread.
            if not self.tray_icon.visible:
                threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.on_close(force=True)

    def setup_hotkeys(self):
        if keyboard:
            try:
                keyboard.add_hotkey('f9', self.start_recording_hotkey)
                keyboard.add_hotkey('f10', self.toggle_pause_hotkey)
                keyboard.add_hotkey('f11', self.stop_recording_hotkey)
            except Exception as e:
                print(f"Failed to setup global hotkeys: {e}")

    def start_recording_hotkey(self):
        if not self.is_recording:
            self.window.after(0, self.start_recording)

    def toggle_pause_hotkey(self):
        if self.is_recording:
            if self.is_paused:
                self.window.after(0, self.resume_recording)
            else:
                self.window.after(0, self.pause_recording)

    def stop_recording_hotkey(self):
        if self.is_recording:
            self.window.after(0, self.stop_recording)

    def start_recording(self, icon=None, item=None):
        if self.is_recording:
            return
            
        # Get selected device indices from UI
        self.mic_idx, self.sys_idx = self.window.get_selected_audio_indices()
            
        # Check Region
        mode = self.window.record_mode.get()
        region = None
        
        if mode == "Select Region":
            # Hide main window to select region
            self.window.withdraw()
            RegionSelectionWindow(self.window, self.on_region_selected)
            return
        
        self._start_recording_process(region=None)

    def on_region_selected(self, region):
        self.window.deiconify()
        if region:
            self._start_recording_process(region)
        else:
            print("Region selection cancelled")

    def _start_recording_process(self, region):
        if self.config.get("show_countdown"):
            self.show_countdown(3, lambda: self._initiate_rec(region))
        else:
            self._initiate_rec(region)

    def show_countdown(self, count, callback):
        top = tk.Toplevel(self.window)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        top.attributes('-alpha', 0.8)
        
        sw = top.winfo_screenwidth()
        sh = top.winfo_screenheight()
        top.geometry(f"200x200+{sw//2-100}+{sh//2-100}")
        top.configure(bg='black')
        
        lbl = tk.Label(top, text=str(count), font=("Arial", 72, "bold"), fg="white", bg="black")
        lbl.pack(expand=True)
        
        def update():
            nonlocal count
            count -= 1
            if count > 0:
                lbl.config(text=str(count))
                top.after(1000, update)
            else:
                top.destroy()
                callback()
                
        top.after(1000, update)

    def _initiate_rec(self, region):
        fps = float(self.config.get("fps", 30))
        codec = self.config.get("codec", "MP4V")
        show_cursor = self.config.get("show_cursor", True)
        audio_source = self.config.get("audio_source", "Microphone")
        
        cleanup_temp_files(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.video_recorder = VideoRecorder(
            filename=self.temp_video_path,
            fps=fps,
            region=region,
            codec=codec,
            show_cursor=show_cursor
        )
        
        self.audio_recorder = AudioRecorder(
            filename=self.temp_audio_path,
            source_type=audio_source,
            device_index=self.mic_idx,
            system_device_index=self.sys_idx
        )
        
        self.video_recorder.start()
        self.audio_recorder.start()
        
        self.is_recording = True
        self.is_paused = False
        self.recording_start_time = time.time()
        self.total_pause_duration = 0
        
        self.window.set_recording_state(True)
        
        self.stop_event.clear()
        self.timer_thread = threading.Thread(target=self.update_timer_loop)
        self.timer_thread.start()
        
        if self.config.get("minimize_to_tray"):
            self.hide_window()

    def update_timer_loop(self):
        while not self.stop_event.is_set():
            if self.is_recording and not self.is_paused:
                elapsed = time.time() - self.recording_start_time - self.total_pause_duration
                time_str = str(datetime.timedelta(seconds=int(elapsed)))
                try:
                    self.window.timer_label.configure(text=time_str)
                except:
                    break
            time.sleep(0.5)

    def pause_recording(self, icon=None, item=None):
        if not self.is_recording or self.is_paused:
            return
            
        self.is_paused = True
        self.pause_start_time = time.time()
        
        self.video_recorder.pause()
        self.audio_recorder.pause()
        
        self.window.on_pause()

    def resume_recording(self, icon=None, item=None):
        if not self.is_recording or not self.is_paused:
            return
            
        self.is_paused = False
        pause_duration = time.time() - self.pause_start_time
        self.total_pause_duration += pause_duration
        
        self.video_recorder.resume()
        self.audio_recorder.resume()
        
        self.window.on_pause()

    def stop_recording(self, icon=None, item=None):
        if not self.is_recording:
            return
            
        self.is_recording = False
        self.stop_event.set()
        
        # Show window if hidden
        self.show_window()
        
        self.window.set_processing_state()
        self.window.update()
        
        self.video_recorder.stop()
        self.audio_recorder.stop()
        
        self.process_output()
        
        self.window.set_recording_state(False)
        self.window.timer_label.configure(text="00:00:00")

    def process_output(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self.config.get("filename_prefix", "ScreenRecord")
        output_folder = self.config.get("save_path")
        
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
            except:
                output_folder = os.getcwd()
        
        output_file = os.path.join(output_folder, f"{prefix}_{timestamp}.mp4")
        
        success = merge_audio_video(
            self.temp_video_path,
            self.temp_audio_path,
            output_file
        )
        
        if success:
            self.window.status_label.configure(text=f"Saved: {os.path.basename(output_file)}", text_color="green")
            messagebox.showinfo("Recording Finished", f"Saved to:\n{output_file}")
        else:
            self.window.status_label.configure(text="Error Saving File", text_color="red")
            messagebox.showerror("Error", "Failed to merge audio/video. Check FFmpeg installation.")

    def on_close(self, force=False):
        if not force and self.is_recording:
            if messagebox.askokcancel("Quit", "Recording in progress. Stop and save?"):
                self.stop_recording()
                self.window.destroy()
        else:
            if self.tray_icon:
                self.tray_icon.stop()
            self.window.destroy()
            sys.exit(0)

    def run(self):
        if not check_ffmpeg():
            messagebox.showwarning("FFmpeg Missing", "FFmpeg was not found in PATH.\nAudio merging will fail.\nPlease install FFmpeg.")
            
        self.window.mainloop()

if __name__ == "__main__":
    app = ScreenRecorderApp()
    app.run()
