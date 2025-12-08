########################################
# image_viewer.py
#
# 根幹は Grok 4.1 beta に作らせてみました。
########################################
# pythonモジュール
import os
import threading
import time
import json
import flet as ft
import win32api
import win32con
# 独自モジュール
import clipboard
import themes
import left_panel as lp

SETTING_JSON_FILE = "viewer_settings.json"

####################
# メイン関数
####################
def main(page: ft.Page):
    # 各種パラメータ設定
    page.title = "PNG Image Viewer with Metadata"
    page.window.min_width = 1024
    page.window.min_height = 576
    page.window.width  = 1440
    page.window.height = 810
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0
    page.navigation_history = ["<DRIVES>"] # 訪問したフォルダの履歴
    page.history_index = 0                 # 現在の位置
    page.window.prevent_close = True
    settings = {}
    theme_colors = themes.ThemeColors.light() #とりあえずの初期値

    ####################
    # 各種イベント処理
    ####################
    # イベント処理：ウインドウを閉じる
    def window_event(e):
        if e.data == "close":
            with open(SETTING_JSON_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            page.window.prevent_close = False
            page.window.close()
    # イベント処理：テーマ切り替えのスイッチ
    def toggle_theme(e):
        if e.data == 'true':
            settings["dark_theme"] = True
        else:
            settings["dark_theme"] = False
        themes.apply_theme(
            page, settings, 
            left_panel, center_panel, right_panel, 
            current_path_text, metadata_text, dir_list, theme_colors)
    # イベント処理：右クリックメニュー
    def show_image_context_menu(e: ft.TapDownEvent):
        if not image_view.src or not os.path.exists(image_view.src):
            return
        menu_x = e.global_x
        menu_y = e.global_y
        # 自前で作るコンテキストメニュー（ポップアップ風）
        context_menu = ft.Container(
            width=240,
            bgcolor=ft.Colors.with_opacity(0.98, ft.Colors.SURFACE),
            border_radius=8,
            shadow=ft.BoxShadow(
                blur_radius=16,
                color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                offset=(0, 4),
            ),
            padding=4,
            content=ft.Column([
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.COPY_ALL, size=18),
                    title=ft.Text("画像をクリップボードにコピー\n(透明度維持)", size=12),
                    on_click=lambda e: (
                        clipboard.copy_image_to_clipboard(page, image_view.src, True),
                        page.overlay.remove(overlay),
                        page.update()
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.COPY, size=18),
                    title=ft.Text("画像をクリップボードにコピー\n(透明度なし)", size=12),
                    on_click=lambda e: (
                        clipboard.copy_image_to_clipboard(page, image_view.src, False),
                        page.overlay.remove(overlay),
                        page.update()
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER_OPEN, size=18),
                    title=ft.Text("フォルダをエクスプローラーで開く", size=12),
                    on_click=lambda e: (
                        os.startfile(os.path.dirname(image_view.src)),
                        page.overlay.remove(overlay),
                        page.update()
                    ),
                ),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CLOSE, size=18),
                    title=ft.Text("キャンセル", size=12, color=ft.Colors.ERROR),
                    on_click=lambda e: (
                        page.overlay.remove(overlay),
                        page.update()
                    ),
                ),
            ], spacing=0),
        )
        # ポップアップとして表示（Stackでオーバーレイ）
        overlay = ft.Stack([
            ft.Container(
                bgcolor=ft.Colors.TRANSPARENT,
                on_click=lambda e: (
                    page.overlay.remove(overlay),
                    page.update()
                ),
                expand=True,
            ),
            ft.Container(
                content=context_menu,
                top=menu_y,
                left=menu_x,
                animate=ft.Animation(150, "decelerate"),
            ),
        ], expand=True)
        page.overlay.append(overlay)
        context_menu.open = True
        page.update()
    # イベント処理：戻る
    def go_back():
        if page.history_index > 0:
            page.history_index -= 1
            lp.refresh_directory(page, page.navigation_history[page.history_index], current_path_text, theme_colors, dir_list, image_view, settings)
    async def async_go_back():
        go_back()
        page.update()
    # イベント処理：進む
    def go_forward():
        if page.history_index + 1 < len(page.navigation_history):
            page.history_index += 1
            lp.refresh_directory(page, page.navigation_history[page.history_index], current_path_text, theme_colors, dir_list, image_view, settings)
    async def async_go_forward():
        go_forward()
        page.update()
    # イベント処理：マウス
    def on_mouse_event(e: ft.MouseEvent):
        if e.button == ft.MouseButton.BACK:
            go_back()
        elif e.button == ft.MouseButton.FORWARD:
            go_forward()
    # イベントリスナー：マウス
    def start_mouse_back_forward_listener():
        if not win32api:
            return
        def listener():
            while True:
                if win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:  # 戻るボタン
                    page.run_task(async_go_back)  # 安全にメインスレッドで実行
                    while win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:
                        time.sleep(0.01)
                    time.sleep(0.08)
                if win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:  # 進むボタン
                    page.run_task(async_go_forward)
                    while win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:
                        time.sleep(0.01)
                    time.sleep(0.08)
                time.sleep(0.01)
        threading.Thread(target=listener, daemon=True).start()
    # マウスイベントの指定
    page.on_mouse_event = on_mouse_event
    # ウインドウイベントの指定
    page.window.on_event = window_event

    ####################
    # 主処理開始
    ####################
    # 起動時にイベントリスナー開始
    start_mouse_back_forward_listener()

    # 設定読み込み
    if os.path.exists(SETTING_JSON_FILE):
        #読む
        with open(SETTING_JSON_FILE) as f:
            settings = json.load(f)
    else:
        #なかったら初期設定をする
        settings['dark_theme'] = False
    theme_colors = themes.ThemeColors.dark() if settings['dark_theme'] else themes.ThemeColors.light()

    # ── 左ペイン：テーマ切り替えスイッチ、ファイルブラウザ ──
    theme_switch = ft.Switch(
        value=settings["dark_theme"],
        on_change=toggle_theme,
        label="ダークモード",
        label_position=ft.LabelPosition.LEFT,
        height=36,
    )
    current_path_text = ft.Text("", size=12, italic=False, color=ft.Colors.OUTLINE)
    dir_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    # ── 中央：画像表示 ──
    image_view = ft.Image(
        src="",
        fit=ft.ImageFit.CONTAIN,
        expand=True,
    )
    image_container = ft.GestureDetector(
        content=image_view,
        on_secondary_tap_down=show_image_context_menu,
    )
    # ── 右ペイン：メタデータ ──
    metadata_text = ft.Column([
        ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
        ft.Text("画像を選択してください", size=18),
        ], scroll=ft.ScrollMode.AUTO, expand=True
    )

    # ── 最終レイアウト
    left_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.EXPLORE),
                ft.Text("ファイルブラウザ", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                theme_switch,
            ]),
            current_path_text,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            dir_list,
        ], expand=True),
        padding=10,
        width=340,
    )
    center_panel = ft.Container(
        content=image_container,
        alignment=ft.alignment.center,
        expand=2,
        bgcolor=theme_colors["bg_main"],
    )
    right_panel = ft.Container(
        content=ft.Column([
            ft.Text("画像情報", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLUE_ACCENT_200),
            metadata_text,
        ], expand=True),
        padding=15,
        width=400,
    )
    page.add(
        ft.Row([
            left_panel,
            center_panel,
            right_panel,
        ], expand=True, spacing=0)
    )
    # 起動時にテーマ適用
    themes.apply_theme(
        page, settings, 
        left_panel, center_panel, right_panel, 
        current_path_text, metadata_text, dir_list, theme_colors)
    # 起動時にドライブ一覧表示
    lp.show_drives(page, metadata_text, current_path_text, theme_colors, dir_list, image_view, settings)
#起動処理
ft.app(target=main)