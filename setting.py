########################################
# settings.py
#
# 設定(人力でコード分割)
########################################
import os
import json

# 定数
SETTING_JSON_FILE = "viewer_settings.json"

####################
# 設定ファイル読み込み
####################
def read():
    settings = {}
    if os.path.exists(SETTING_JSON_FILE):
        with open(SETTING_JSON_FILE) as f:
            settings = json.load(f)
    else:
        settings['dark_theme'] = False
    return settings

####################
# 設定ファイル保存
####################
def save(settings):
    with open(SETTING_JSON_FILE, 'w') as f:
        json.dump(settings, f, indent=4)