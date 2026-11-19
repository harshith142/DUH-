"""
Configuration settings for Bahubali Desktop Buddy.
"""

import os
import json

CONFIG_DIR = os.path.expanduser("~/.duh_buddy")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "name": "Bahubali",
    "walk_speed": 4,             # Pixels per step
    "fps": 24,                   # Animation frame rate
    "voice_rate": 1,             # SAPI speech rate (-10 to 10)
    "voice_volume": 100,         # Speech volume (0 to 100)
    "voice_index": 1,            # 0: David, 1: Zira
    "energy_threshold": 500,     # Microphone sensitivity
    "auto_walk": True,           # Walk autonomously along bottom
    "screen_margin": 40,         # Distance from bottom (above taskbar)
    "ipc_port": 18899,           # Local IPC TCP port
    "bubble_timeout": 6,         # Seconds speech bubble remains visible
    "whisper_model": "base",     # Whisper model: tiny, base, small, medium, large
    "wake_words": ["hey bahubali", "bahubali", "hey baahubali", "baahubali", "hey buddy"]  # Wake words for voice activation
}


def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        print(f"[Config Save Error] {e}")
