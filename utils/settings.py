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
        # 最後の状態記憶
        if "memory" not in settings:
            settings["memory"] = {}
        if "last_dir" not in settings["memory"]:
            settings["memory"]["last_dir"] = "<DRIVES>"
        # オプション
        if "settings" not in settings:
            settings["settings"] = {}
        if "dark_theme" not in settings["settings"]:
            settings["settings"]["dark_theme"] = False
        if "read_stealth_png_info" not in settings["settings"]:
            settings["settings"]["read_stealth_png_info"] = True
        return settings
    @staticmethod
    def save(settings):
        with open(SETTING_JSON_FILE, 'w') as f:
            json.dump(settings, f, indent=4)