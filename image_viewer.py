########################################
# image_viewer.py
#
# これが本体。
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
import win32gui
# 独自モジュール
import themes
import left_panel as lp
import center_panel as cp

SETTING_JSON_FILE = "viewer_settings.json"

####################
# メイン関数
####################
def main(page: ft.Page):
    # pageパラメータ設定(標準)
    page.title = "PNG Image Viewer with Metadata"
    page.window.min_width = 1024
    page.window.min_height = 576
    page.window.width  = 1440
    page.window.height = 810
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0
    page.window.prevent_close = True
    #pageパラメータ(カスタム)
    page.navigation_history = ["<DRIVES>"] # 訪問したフォルダの履歴
    page.history_index = 0                 # 現在の位置
    page.current_image_path = None         # 現在の画像のパス
    page.scroll_position_history = []      # ファイルブラウザのスクロール位置履歴
    #その他
    settings = {}
    theme_colors = themes.ThemeColors.light() #とりあえずの初期値

    ####################
    # 各種イベント処理
    ####################
    # イベント処理：ウインドウハンドルを取得
    def setup_window_handle():
        import win32gui
        time.sleep(0.6)
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and page.title in win32gui.GetWindowText(hwnd):
                page.window_handle = hwnd
                return False
        win32gui.EnumWindows(callback, None)
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
    # イベント処理：画像右クリックメニュー
    def show_image_context_menu(e: ft.TapDownEvent):
        # サムネイルグリッド表示中 or 画像非表示はメニューを出さない
        if thumbnail_grid.visible or not image_view.visible:
            return
        current_path = getattr(page, "current_image_path", None)
        # 画像のパスがない時もメニューを出さない
        if not current_path or not os.path.exists(current_path):
            return
        menu_x = e.global_x
        menu_y = e.global_y
        # UI作成
        cp.create_image_context_menu(page, menu_x, menu_y, current_path)

    # イベント処理：グリッド表示に戻る
    def return_to_grid(e):
        if image_view.visible:
            thumbnail_grid.visible = True
            image_view.visible = False
            page.current_image_path = None
            # すべてのサムネイルの拡大をリセット！
            for container in thumbnail_grid.controls:
                if hasattr(container, "animate_scale") and container.scale != 1.0:
                    container.scale = 1.0
                    container.update()
            # メタデータもサムネイルビュー用のに戻す
            metadata_text.controls.clear()
            metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text(f"サムネイルビュー: {len(thumbnail_grid.controls)} 枚", 
                        size=16, weight=ft.FontWeight.BOLD),
                ft.Text(page.navigation_history[page.history_index], 
                        size=12, color=ft.Colors.OUTLINE),
            ])
            page.update()
    # ファイルブラウザのスクロール位置記録(人力実装)
    def get_scroll_offset(e):
        scroll_pos = json.loads(e.data)
        if scroll_pos["t"] == "end":
            tmpInfo = {current_path_text.value:{"scroll_pos":scroll_pos["p"], "window_height":page.window.height}}
            #print("tmpInfo:"+str(tmpInfo))
            overwrited = False
            for index, item in enumerate(page.scroll_position_history):
                if current_path_text.value in item:
                    if scroll_pos["p"] > 0:
                        page.scroll_position_history[index] = tmpInfo
                        #print("同じ場所記録済みかつPOS:0以上なのでなので上書き")
                    else:
                        page.scroll_position_history.pop(index)
                        #print("同じ場所記録済みかつPOS:0なので履歴を削除")
                    overwrited = True #消してもTrueにする
                    break
            if overwrited == False:
                if scroll_pos["p"] > 0:
                    page.scroll_position_history.append(tmpInfo)
                    #print("同じ場所がないかつPOS:0以上なので追加")
            #print(page.scroll_position_history)
    # イベント処理：戻る
    def go_back():
        if page.history_index > 0:
            page.history_index -= 1
            lp.refresh_directory(page, page.navigation_history[page.history_index], metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
    async def async_go_back():
        go_back()
        page.update()
    # イベント処理：進む
    def go_forward():
        if page.history_index + 1 < len(page.navigation_history):
            page.history_index += 1
            lp.refresh_directory(page, page.navigation_history[page.history_index], metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
    async def async_go_forward():
        go_forward()
        page.update()
    # イベントリスナー：マウス
    def start_mouse_back_forward_listener():
        def listener():
            while True:
                # ハンドルがまだ取得できてなかったら待つ
                if not hasattr(page, "window_handle") or not page.window_handle:
                    time.sleep(0.1)
                    continue
                if win32gui.GetForegroundWindow() == page.window_handle:
                    # 戻る
                    if win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:
                        page.run_task(async_go_back)
                        while win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:
                            time.sleep(0.01)
                        time.sleep(0.08)
                    # 進む
                    if win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:
                        page.run_task(async_go_forward)
                        while win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:
                            time.sleep(0.01)
                        time.sleep(0.08)
                time.sleep(0.01)
        threading.Thread(target=listener, daemon=True).start()

    ####################
    # 主処理開始
    ####################
    # ウインドウハンドルの監視をバックグラウンドで実行
    threading.Thread(target=setup_window_handle, daemon=True).start()
    # ウインドウイベントの指定
    page.window.on_event = window_event
    # 起動時にイベントリスナー開始
    start_mouse_back_forward_listener()

    # 設定読み込み(ない場合は初期設定をする)
    if os.path.exists(SETTING_JSON_FILE):
        with open(SETTING_JSON_FILE) as f:
            settings = json.load(f)
    else:
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
    dir_list = ft.ListView(
        expand=True,
        spacing=0,
        padding=0,
        on_scroll=get_scroll_offset,
    )
    # ── 中央：サムネイルグリッド、画像表示 ──
    image_view = ft.Image(
        src="",
        fit=ft.ImageFit.CONTAIN,
        expand=True,
        visible=False,
    )
    thumbnail_grid = ft.GridView(
        runs_count=5,
        max_extent=180,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
        padding=20,
        visible=False,
    )
    center_content_stack = ft.Stack([
        image_view,
        thumbnail_grid,
    ], expand=True)
    center_container = ft.GestureDetector(
        content=center_content_stack,
        on_secondary_tap_down=show_image_context_menu,
        on_tap_down=return_to_grid,
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
        content=center_container,
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
    # ローディングオーバーレイ（最初は非表示）
    loading_overlay = ft.Container(
        visible=False,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
        alignment=ft.alignment.center,
        content=ft.Column([
            ft.ProgressRing(width=60, height=60, stroke_width=7, color=ft.Colors.CYAN_400),
            ft.Text("読み込み中…", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24),
    )
    # page.overlay に追加（最前面に常に表示）
    page.overlay.append(loading_overlay)
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
    lp.show_drives(page, metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
#起動処理
ft.app(target=main)