import os
import json
import platform

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "save_path": os.path.join(os.path.expanduser("~"), "Videos"),
    "resolution": "1080p",
    "fps": 30,
    "quality": "Medium",
    "codec": "MP4V",
    "audio_source": "Microphone + System",
    "mic_volume": 80,
    "system_volume": 100,
    "show_cursor": True,
    "show_countdown": True,
    "minimize_to_tray": False,
    "auto_merge": True,
    "filename_prefix": "ScreenRecord"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            full_config = DEFAULT_CONFIG.copy()
            full_config.update(config)
            return full_config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_default_output_folder():
    return DEFAULT_CONFIG["save_path"]
