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
        
        # Initialize mss
        self.sct = mss.mss()
        
        # Determine capture area
        if self.region:
            self.monitor = {
                "top": int(self.region[1]),
                "left": int(self.region[0]),
                "width": int(self.region[2]),
                "height": int(self.region[3])
            }
        else:
            # Full screen - monitor 1 usually
            monitor = self.sct.monitors[1]
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
        self.sct.close()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        
    def _record(self):
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        out = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))
        
        frame_time = 1.0 / self.fps
        
        self.start_time = time.time()
        
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
                
            # Maintain FPS
            process_time = time.time() - loop_start
            wait_time = frame_time - process_time
            if wait_time > 0:
                time.sleep(wait_time)
                
        out.release()

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
