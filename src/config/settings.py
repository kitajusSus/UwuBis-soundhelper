
import json
import os

DEFAULT_CONFIG = {
    "DEFAULT_SEGMENT_DURATION": 5,
    "WORDS_PER_CHAPTER": 5,
    "RESULTS_FOLDER": "wyniki/",
    "AUDIO_FOLDER": "audio/demony/",
    "SPEAKING_TIME": 10
}

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config if not exists
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)