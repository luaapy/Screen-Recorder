import numpy as np
import wave
import threading
import time
import platform
import sys

# Handle optional sounddevice dependency
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except OSError:
    HAS_SOUNDDEVICE = False
    sd = None

class AudioRecorder:
    def __init__(self, filename="temp_audio.wav", samplerate=44100, channels=2, source_type="Microphone", device_index=None, system_device_index=None):
        """
        :param source_type: "Microphone", "System Audio", "Both", "None"
        :param device_index: Index for Microphone
        :param system_device_index: Index for System Audio (Loopback)
        """
        self.filename = filename
        self.samplerate = samplerate
        self.channels = channels
        self.source_type = source_type
        self.mic_device = device_index
        self.sys_device = system_device_index
        
        self.recording = False
        self.paused = False
        self._thread = None
        self._frames = [] # Stored as list of numpy arrays
        
        self.is_windows = platform.system() == "Windows"
        
        if not HAS_SOUNDDEVICE:
            print("Warning: PortAudio/sounddevice not found. Audio recording will be disabled.")

    @staticmethod
    def get_devices(kind=None):
        """Returns a list of available audio devices."""
        if not HAS_SOUNDDEVICE:
            return []
        try:
            devices = sd.query_devices()
            device_list = []
            for i, d in enumerate(devices):
                # Filter by kind if needed ('input' or 'output')
                if kind == 'input' and d['max_input_channels'] > 0:
                    device_list.append({'index': i, 'name': d['name'], 'hostapi': d['hostapi']})
                elif kind == 'output' and d['max_output_channels'] > 0: # For loopback lookups
                     device_list.append({'index': i, 'name': d['name'], 'hostapi': d['hostapi']})
                elif kind is None:
                    device_list.append(d)
            return device_list
        except Exception:
            return []

    def start(self):
        if self.recording:
            return
            
        if not HAS_SOUNDDEVICE or self.source_type == "None":
            return

        self.recording = True
        self._frames = []
        self._thread = threading.Thread(target=self._record)
        self._thread.start()
        
    def stop(self):
        if not self.recording:
            return
            
        self.recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
            
        self._save_file()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        
    def _record(self):
        """
        Handles recording based on source type.
        """
        try:
            if self.source_type == "Microphone":
                self._record_stream(self.mic_device, is_loopback=False)
            elif self.source_type == "System Audio":
                # On Windows, WASAPI Loopback requires specific handling
                self._record_stream(self.sys_device, is_loopback=True)
            elif self.source_type == "Both":
                self._record_mixed(self.mic_device, self.sys_device)
        except Exception as e:
            print(f"Recording error: {e}")
            self.recording = False

    def _record_stream(self, device, is_loopback=False):
        def callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if not self.paused:
                self._frames.append(indata.copy())

        # Determine input device parameters
        try:
            extra_settings = {}
            if self.is_windows and is_loopback:
                # To record system audio on Windows, we usually need to find the WASAPI loopback device.
                # 'sounddevice' supports loopback via valid device index if it supports WASAPI.
                # Ensure the device passed is indeed a loopback-capable device or use 'loopback=True' if supported by newer sd versions directly?
                # Actually, sounddevice requires finding the loopback device manually usually, but recent versions handle WASAPI loopback if using the 'wasapi' hostapi.
                pass 

            with sd.InputStream(samplerate=self.samplerate,
                                channels=self.channels,
                                device=device,
                                callback=callback,
                                **extra_settings):
                while self.recording:
                    sd.sleep(100)
        except Exception as e:
            print(f"Stream error: {e}")

    def _record_mixed(self, mic_idx, sys_idx):
        # For mixed recording, we need two streams.
        # This is complex because streams are blocking or callback-based.
        # We will use two separate lists and merge them later, or use non-blocking callbacks to a shared buffer.
        
        mic_frames = []
        sys_frames = []
        
        def mic_callback(indata, frames, time, status):
            if not self.paused:
                mic_frames.append(indata.copy())
                
        def sys_callback(indata, frames, time, status):
            if not self.paused:
                sys_frames.append(indata.copy())

        try:
            stream_mic = sd.InputStream(samplerate=self.samplerate, channels=self.channels, device=mic_idx, callback=mic_callback)
            stream_sys = sd.InputStream(samplerate=self.samplerate, channels=self.channels, device=sys_idx, callback=sys_callback)
            
            with stream_mic, stream_sys:
                while self.recording:
                    sd.sleep(100)
                    
            # Post-process merge
            self._merge_frames(mic_frames, sys_frames)
            
        except Exception as e:
            print(f"Mixed recording error: {e}")

    def _merge_frames(self, frames1, frames2):
        # Simple merge: ensure same length and add
        # This is a naive implementation; desync might occur over long periods if clocks differ
        len1 = sum(len(f) for f in frames1)
        len2 = sum(len(f) for f in frames2)
        
        # Concatenate first
        arr1 = np.concatenate(frames1) if frames1 else np.zeros((0, self.channels), dtype=np.float32)
        arr2 = np.concatenate(frames2) if frames2 else np.zeros((0, self.channels), dtype=np.float32)
        
        # Trim to shorter
        min_len = min(len(arr1), len(arr2))
        if min_len == 0:
            # Fallback if one failed
            self._frames = [arr1] if len(arr1) > 0 else [arr2]
            return

        arr1 = arr1[:min_len]
        arr2 = arr2[:min_len]
        
        # Mix (average or add and clip)
        mixed = (arr1 + arr2) / 2
        self._frames = [mixed]

    def _save_file(self):
        if not self._frames:
            return
            
        try:
            # Concatenate all blocks if not already done
            if isinstance(self._frames[0], np.ndarray):
                recording_data = np.concatenate(self._frames, axis=0)
            else:
                recording_data = np.array(self._frames)
            
            # Scale
            if recording_data.dtype == np.float32:
                recording_data = (recording_data * 32767).astype(np.int16)
            
            with wave.open(self.filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.samplerate)
                wf.writeframes(recording_data.tobytes())
        except Exception as e:
            print(f"Error saving audio: {e}")
