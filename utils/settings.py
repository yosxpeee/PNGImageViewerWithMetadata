import os
import json

SETTING_JSON_FILE = "viewer_settings.json"

class SettingsManager:
    @staticmethod
    def load():
        settings = {}
        if os.path.exists(SETTING_JSON_FILE):
            with open(SETTING_JSON_FILE, 'r') as f:
                settings = json.load(f)
        if "dark_theme" not in settings:
            settings["dark_theme"] = False
        if "last_dir" not in settings:
            settings["last_dir"] = "<DRIVES>"
        return settings
    @staticmethod
    def save(settings):
        with open(SETTING_JSON_FILE, 'w') as f:
            json.dump(settings, f, indent=4)