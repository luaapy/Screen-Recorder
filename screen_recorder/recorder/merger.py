import os
import subprocess
import shutil
import platform
import threading
import glob

def find_ffmpeg():
    """Find the ffmpeg executable path."""
    # First check if ffmpeg is in PATH
    try:
        result = subprocess.run(["where", "ffmpeg"] if platform.system() == "Windows" else ["which", "ffmpeg"], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            return "ffmpeg"
    except:
        pass
    
    # On Windows, check WinGet install location
    if platform.system() == "Windows":
        winget_paths = glob.glob(os.path.expanduser(
            r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe"
        ))
        if winget_paths:
            return winget_paths[0]
        
        # Also check common install locations
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    
    return None

# Cache the ffmpeg path
_ffmpeg_path = None

def get_ffmpeg_path():
    """Get the cached ffmpeg path or find it."""
    global _ffmpeg_path
    if _ffmpeg_path is None:
        _ffmpeg_path = find_ffmpeg()
    return _ffmpeg_path

def check_ffmpeg():
    """Checks if ffmpeg is available."""
    ffmpeg = get_ffmpeg_path()
    if ffmpeg is None:
        return False
    try:
        subprocess.run([ffmpeg, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_temp_dir():
    """Returns the temporary directory for the application."""
    if platform.system() == "Windows":
        temp_dir = os.path.join(os.environ.get("TEMP", os.getcwd()), "screen_recorder")
    else:
        temp_dir = os.path.join("/tmp", "screen_recorder")
    
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def merge_audio_video(video_path, audio_path, output_path, keep_temp=False):
    """
    Merges audio and video files using ffmpeg.
    :param video_path: Path to the video file
    :param audio_path: Path to the audio file
    :param output_path: Path for the final output file
    :param keep_temp: Whether to keep temporary files after merge
    :return: True if successful, False otherwise
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
        
    if not os.path.exists(audio_path):
        # If no audio file, just copy/move video to output
        try:
            shutil.move(video_path, output_path)
            return True
        except Exception as e:
            print(f"Error moving video file: {e}")
            return False

    # Get ffmpeg path
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        print("Error: FFmpeg not found. Please install FFmpeg.")
        return False

    # Read actual FPS from companion file if it exists
    fps_file = video_path + ".fps"
    actual_fps = None
    if os.path.exists(fps_file):
        try:
            with open(fps_file, 'r') as f:
                actual_fps = float(f.read().strip())
            print(f"Using actual captured FPS: {actual_fps}")
            os.remove(fps_file)  # Clean up
        except:
            pass

    # Construct ffmpeg command
    # Re-encode to H.264 for maximum compatibility
    cmd = [ffmpeg, "-y"]
    
    # Add video input with correct framerate interpretation
    # Use -itsscale to slow down the video if actual FPS is lower than expected
    if actual_fps and actual_fps < 25:
        # Calculate scale factor: if recorded at 8 fps but video says 30, we need to slow it down
        # itsscale makes the video play slower (higher value = slower)
        scale_factor = 30.0 / actual_fps  # e.g., 30/8 = 3.75x slower
        cmd.extend(["-itsscale", str(scale_factor)])
    
    cmd.extend(["-i", video_path])
    
    # Add audio input
    cmd.extend(["-i", audio_path])
    
    # Map both streams explicitly
    cmd.extend([
        "-map", "0:v:0",  # First video stream from first input
        "-map", "1:a:0",  # First audio stream from second input
        "-c:v", "libx264",  # Re-encode to H.264 for compatibility
        "-preset", "fast",  # Faster encoding
        "-crf", "23",  # Quality (lower = better, 18-28 is good range)
        "-r", "30",  # Output at 30 FPS for smooth playback
        "-c:a", "aac",
        "-b:a", "192k",  # Audio bitrate
        "-ar", "44100",  # Audio sample rate
        "-ac", "2",  # Stereo audio
        "-movflags", "+faststart",  # Enable streaming/quick playback
        output_path
    ])
    
    try:
        # Run ffmpeg
        # On Windows, we might want to hide the console window
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        print(f"Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        
        if result.returncode == 0:
            # Verify output file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Successfully created: {output_path} ({os.path.getsize(output_path)} bytes)")
                if not keep_temp:
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                return True
            else:
                print(f"Error: Output file not created or empty: {output_path}")
                return False
        else:
            print(f"FFmpeg merge failed (code {result.returncode}): {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Error executing ffmpeg: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_temp_files(folder):
    """Cleans up the temporary folder."""
    try:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    except Exception as e:
        print(f"Error cleaning temp files: {e}")

if __name__ == "__main__":
    print(f"FFmpeg Available: {check_ffmpeg()}")
    print(f"Temp Dir: {get_temp_dir()}")
