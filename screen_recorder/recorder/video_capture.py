import cv2
import numpy as np
import mss
import time
import threading
import platform
import os

HAS_PYAUTOGUI = False
try:
    # Check for DISPLAY on Linux to avoid immediate crash on import
    if platform.system() == "Linux" and "DISPLAY" not in os.environ:
        raise ImportError("No DISPLAY")
    
    import pyautogui
    HAS_PYAUTOGUI = True
except (ImportError, KeyError, Exception):
    HAS_PYAUTOGUI = False

class VideoRecorder:
    def __init__(self, filename="temp_video.avi", fps=30.0, resolution=None, region=None, codec="XVID", show_cursor=True):
        self.filename = filename
        self.fps = float(fps)
        self.codec = codec
        self.show_cursor = show_cursor
        
        self.region = region  # (left, top, width, height)
        self.resolution = resolution
        
        self.recording = False
        self.paused = False
        self.stop_event = threading.Event()
        self.start_time = None
        self.elapsed_time = 0
        self._thread = None
        self.sct = None  # Will be created in recording thread
        
        # Get monitor info for dimensions (temporary mss instance)
        with mss.mss() as temp_sct:
            if self.region:
                self.monitor = {
                    "top": int(self.region[1]),
                    "left": int(self.region[0]),
                    "width": int(self.region[2]),
                    "height": int(self.region[3])
                }
            else:
                # Full screen - monitor 1 usually
                monitor = temp_sct.monitors[1]
                self.monitor = {
                    "top": monitor["top"],
                    "left": monitor["left"],
                    "width": monitor["width"],
                    "height": monitor["height"]
                }

        self.width = self.monitor["width"]
        self.height = self.monitor["height"]
        
    def start(self):
        if self.recording:
            return
            
        self.recording = True
        self.stop_event.clear()
        self._thread = threading.Thread(target=self._record)
        self._thread.start()
        
    def stop(self):
        if not self.recording:
            return
            
        self.stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join()
        
        self.recording = False
        # sct is closed inside _record thread

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        
    def _record(self):
        # Create mss instance inside the recording thread to avoid threading issues
        self.sct = mss.mss()
        
        # Use XVID codec which is more reliable
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))
        
        if not out.isOpened():
            print(f"Error: Could not open video writer with codec {self.codec}")
            self.sct.close()
            return
        
        frame_time = 1.0 / self.fps
        frame_count = 0
        
        self.start_time = time.time()
        
        try:
            while not self.stop_event.is_set():
                loop_start = time.time()
                
                if not self.paused:
                    # Capture frame
                    img = self.sct.grab(self.monitor)
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # Draw cursor
                    if self.show_cursor and HAS_PYAUTOGUI:
                        self._draw_cursor(frame)

                    out.write(frame)
                    frame_count += 1
                    
                # Maintain FPS - wait to match target frame time
                process_time = time.time() - loop_start
                wait_time = frame_time - process_time
                if wait_time > 0:
                    time.sleep(wait_time)
        finally:
            out.release()
            self.sct.close()
            
            # Calculate actual FPS
            total_time = time.time() - self.start_time
            self.actual_fps = frame_count / total_time if total_time > 0 else self.fps
            self.frame_count = frame_count
            self.total_time = total_time
            print(f"Video recording complete: {frame_count} frames in {total_time:.1f}s (actual FPS: {self.actual_fps:.1f})")
            
            # Save actual FPS to companion file for FFmpeg
            fps_file = self.filename + ".fps"
            with open(fps_file, 'w') as f:
                f.write(f"{self.actual_fps:.2f}")

    def _draw_cursor(self, frame):
        try:
            # Get absolute cursor position
            x, y = pyautogui.position()
            
            # Adjust to relative if region recording
            rel_x = x - self.monitor["left"]
            rel_y = y - self.monitor["top"]
            
            # Check bounds
            if 0 <= rel_x < self.width and 0 <= rel_y < self.height:
                # Draw a simple circle or arrow
                # Simple red circle with black outline
                cv2.circle(frame, (rel_x, rel_y), 5, (0, 0, 255), -1) 
                cv2.circle(frame, (rel_x, rel_y), 5, (0, 0, 0), 1)
        except Exception:
            pass # Fail silently if cursor fetch fails

    def get_duration(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
