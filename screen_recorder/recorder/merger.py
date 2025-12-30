import os
import subprocess
import shutil
import platform
import threading

def check_ffmpeg():
    """Checks if ffmpeg is available in the system PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
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

    # Construct ffmpeg command
    # -c:v copy -c:a aac -strict experimental
    cmd = [
        "ffmpeg",
        "-y", # Overwrite output
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest", # Finish when shortest stream ends
        output_path
    ]
    
    try:
        # Run ffmpeg
        # On Windows, we might want to hide the console window
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        
        if result.returncode == 0:
            if not keep_temp:
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            return True
        else:
            print(f"FFmpeg merge failed: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Error executing ffmpeg: {e}")
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
