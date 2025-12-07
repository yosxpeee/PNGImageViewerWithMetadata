########################################
# image_viewer.py
#
# 根幹は Grok 4.1 beta に作らせてみました。
########################################
import os
import io
import string
import png
import threading
import time
import struct
import json
import flet as ft
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image
import win32clipboard
import win32api
import win32con

BITMAPV5HEADER_SIZE = 124
SETTING_JSON_FILE = "viewer_settings.json"

####################
# カラーテーマ定義
####################
class ThemeColors:
    @staticmethod
    def light():
        return {
            "bg_main": ft.Colors.WHITE,
            "bg_panel": ft.Colors.WHITE,
            "text_primary": ft.Colors.BLACK,
            "text_secondary": ft.Colors.OUTLINE,
            "divider": ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE),
            "hover": ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            "selected": ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
            "surface": ft.Colors.SURFACE,
            "meta_secondary_title": ft.Colors.TEAL_900,
        }
    @staticmethod
    def dark():
        return {
            "bg_main": ft.Colors.with_opacity(0.98, "#0e0e0e"),   # ほぼ真っ黒
            "bg_panel": ft.Colors.with_opacity(0.96, "#121212"),  # 少し明るめのカード
            "text_primary": ft.Colors.WHITE,
            "text_secondary": ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            "divider": ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            "hover": ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            "selected": ft.Colors.with_opacity(0.22, ft.Colors.WHITE),
            "surface": ft.Colors.with_opacity(0.98, "#1e1e1e"),
            "meta_secondary_title": ft.Colors.TEAL_ACCENT_400,
        }

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
    theme_colors = ThemeColors.light() #とりあえずの初期値

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
        apply_theme()
    # イベント処理：テキストをクリップボードへコピー
    def copy_to_clipboard(text: str, name: str = "テキスト"):
        page.set_clipboard(text)
        snack = ft.SnackBar(
            content=ft.Text(f"{name}をコピーしました！"),
            bgcolor=ft.Colors.GREEN_700,
            duration=1500,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    # イベント処理：履歴のナビゲート
    def navigate_to(path: str):
        if page.history_index + 1 < len(page.navigation_history):
            page.navigation_history = page.navigation_history[:page.history_index + 1]
        page.navigation_history.append(path)
        page.history_index += 1
        refresh_directory(path)
    # イベント処理：戻る
    def go_back():
        if page.history_index > 0:
            page.history_index -= 1
            refresh_directory(page.navigation_history[page.history_index])
    async def async_go_back():
        go_back()
        page.update()
    # イベント処理：進む
    def go_forward():
        if page.history_index + 1 < len(page.navigation_history):
            page.history_index += 1
            refresh_directory(page.navigation_history[page.history_index])
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
    # テーマ変更処理
    ####################
    def _walk_and_color(control):
        """再帰的に色を適用（必要に応じて追加）"""
        if hasattr(control, "color") and control.color in (ft.Colors.BLACK, ft.Colors.WHITE, ft.Colors.OUTLINE):
            if isinstance(control, ft.Text):
                control.color = theme_colors["text_primary"] if control.weight == ft.FontWeight.BOLD else theme_colors["text_secondary"]
        if hasattr(control, "bgcolor"):
            if control == dir_list:
                return
            # ホバー用コンテナは別途処理
            if isinstance(control, ft.Container) and control.ink:
                pass
        if hasattr(control, "controls"):
            for child in control.controls:
                _walk_and_color(child)
    def apply_theme():
        theme_colors = ThemeColors.dark() if settings["dark_theme"] else ThemeColors.light()
        page.theme_mode = ft.ThemeMode.DARK if settings["dark_theme"] else ft.ThemeMode.LIGHT
        page.bgcolor = theme_colors["bg_main"]
        # 中央パネル
        center_panel.bgcolor = theme_colors["bg_main"]
        # 左パネル
        left_panel.bgcolor = theme_colors["bg_panel"]
        left_panel.border = ft.border.all(1, theme_colors["divider"])
        # 右パネル
        right_panel.bgcolor = theme_colors["bg_panel"]
        right_panel.border = ft.border.all(1, theme_colors["divider"])
        # 汎用テキスト系
        current_path_text.color = theme_colors["text_secondary"]
        for ctrl in page.controls:
            if isinstance(ctrl, ft.Row):
                for c in ctrl.controls:
                    _walk_and_color(c)
        # メタデータエリアの区切り線と固有のテキスト
        if metadata_text.controls:
            for c in metadata_text.controls:
                if isinstance(c, ft.Divider):
                    c.color = theme_colors["divider"]
                if isinstance(c, ft.Text):
                    # 変えないと見にくくなるものだけ変更
                    if c.value == "PNG メタデータ" or c.value == "ファイル情報":
                        c.color = theme_colors["meta_secondary_title"]
        page.update()

    ####################
    # 左ペインの処理
    ####################
    # 高さ調整可能＆ホバーエフェクトの汎用アイテム生成
    def make_list_item(name: str, icon, path: str, is_folder=False):
        #クリック時のイベントハンドラ
        def on_click_handler(e):
            if path == "<DRIVES>":
                show_drives()
            elif is_folder:
                navigate_to(path)
            else:
                select_image(path)
        #ホバーエフェクト
        def mli_hover(e):
            container.bgcolor = theme_colors["hover"] if e.data == "true" else None
            container.update()

        container = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=12),
                ft.Text(name, expand=True, size=12),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=12, opacity=0.5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            height=24,
            padding=ft.padding.symmetric(horizontal=1, vertical=1),
            border_radius=8,
            ink=True,
            on_click=on_click_handler,
        )
        container.on_hover = mli_hover
        return container
    # ディレクトリ情報更新
    def refresh_directory(path: str):
        # ホバーエフェクト
        def rd_hover(e):
            back.bgcolor = theme_colors["selected"] if e.data == "true" else None
            back.update()

        dir_list.controls.clear()
        # ドライブ一覧の特別処理
        if path == "<DRIVES>":
            current_path_text.value = "ドライブを選択してください"
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    label = win32api.GetVolumeInformation(drive)[0] or "ドライブ"
                    dir_list.controls.append(make_list_item(f"{drive} [{label}]", ft.Icons.STORAGE, drive, True))
            page.update()
            return
        current_path_text.value = f"現在: {path}"
        p = Path(path)
        # ドライブ一覧に戻る
        back = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.COMPUTER, size=12),
                ft.Text("ドライブ一覧に戻る", expand=True, size=12),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=12, opacity=0.5),
            ]),
            height=24,
            padding=ft.padding.symmetric(horizontal=1, vertical=1),
            border_radius=8,
            ink=True,
            on_click=lambda e: navigate_to("<DRIVES>"),
        )
        back.on_hover = rd_hover
        dir_list.controls.append(back)
        dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),)
        # 親フォルダ
        if p.parent != p:
            dir_list.controls.append(make_list_item(".. (親フォルダ)", ft.Icons.ARROW_BACK, str(p.parent), True))
        try:
            for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    dir_list.controls.append(make_list_item(item.name + "/", ft.Icons.FOLDER, str(item), True))
                elif item.suffix.lower() == ".png":
                    dir_list.controls.append(make_list_item(item.name, ft.Icons.IMAGE, str(item), False))
        except PermissionError:
            dir_list.controls.append(ft.Text("アクセス拒否", color="red"))
        page.update()
    # 画像選択
    def select_image(path: str):
        image_view.src = path
        update_metadata(path)
        page.update()
    # ドライブ一覧表示
    def show_drives():
        # 履歴に追加してrefresh_directoryに任せる
        navigate_to("<DRIVES>")

    ####################
    # 中央ペインの処理
    ####################
    # クリップボードに画像をコピー（透明度あり/なし両対応）
    def copy_image_to_clipboard(image_path: str, alpha: bool):
        try:
            if alpha == True:
                img = Image.open(image_path).convert("RGBA")
                w, h = img.size
                arr = np.array(img)
                bgra = arr[:, :, [2, 1, 0, 3]]     # RとBを入れ替え + Alpha最後
                pixels = np.flipud(bgra).tobytes() # DIBはボトムアップ
                header = struct.pack(
                    "<LllHHLLllLLllllLLllllLLLlLLLLLLLLL",
                    BITMAPV5HEADER_SIZE, # 0
                    w, h, 1, 32,         # 4,8,12,14
                    3, 0, 0, 0, 0, 0, 0, # 16〜36
                    0x00FF0000,          # 40 Red mask
                    0x0000FF00,          # 44 Green mask
                    0x000000FF,          # 48 Blue mask
                    0xFF000000,          # 52 Alpha mask
                    0x73524742,          # 56 LCS_sRGB
                    0,0,0,0,0,0,0,0,0,   # 60-95  endpoints
                    0,0,0,               # 96-107 gamma
                    0,                   # 108 intent
                    0,0,0,0              # 112-124 reserved
                )
                data = header + pixels
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIBV5, data)
                done_msg = "(透明度あり)"
            else:
                img = Image.open(image_path)
                # RGBに変換（透明度がある場合は背景白で合成）
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                output = io.BytesIO()
                img.save(output, format='BMP')
                data = output.getvalue()[14:]  # BMPヘッダー14バイト除去
                output.close()
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                done_msg = "(透明度なし)"
            # PNGも同時登録
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_format = win32clipboard.RegisterClipboardFormat("PNG")
            if png_format:
                win32clipboard.SetClipboardData(png_format, buf.getvalue())
            win32clipboard.CloseClipboard()
            # スナックバーで通知
            snack = ft.SnackBar(
                content=ft.Text("画像をクリップボードにコピーしました！"+done_msg, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                duration=2000,
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception as e:
            snack = ft.SnackBar(
                content=ft.Text(f"コピー失敗: {e}", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                duration=3000,
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
    # 右クリックメニュー
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
                        copy_image_to_clipboard(image_view.src, True),
                        page.overlay.remove(overlay),
                        page.update()
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.COPY, size=18),
                    title=ft.Text("画像をクリップボードにコピー\n(透明度なし)", size=12),
                    on_click=lambda e: (
                        copy_image_to_clipboard(image_view.src, False),
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
                ft.Divider(height=1),
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

    ####################
    # 右ペインの処理
    ####################
    # メタデータ表示の更新
    def update_metadata(image_path: str):
        # パーツ：コピペできるテキスト表示領域
        def make_copyable_text(value: str, size=12):
            return ft.TextField(
                value=value,
                read_only=True,
                multiline=True,
                border="none",
                text_size=size,
                min_lines=1,
                max_lines=100,
            )
        # プロンプト表示領域
        def prompt_textarea():
            metadata_text.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("プロンプト", weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            icon_size=14,
                            tooltip="プロンプトをコピー",
                            on_click=lambda e: copy_to_clipboard(prompt_text, "プロンプト")
                        )
                    ]),
                    padding=ft.padding.only(top=0, bottom=0),
                    border=ft.border.only(
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                        bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                    ),
                )
            )
            metadata_text.controls.append(make_copyable_text(prompt_text, size=11))
        # ネガティブプロンプト表示領域
        def negative_textarea():
            metadata_text.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("ネガティブプロンプト", weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            icon_size=14,
                            tooltip="ネガティブプロンプトをコピー",
                            on_click=lambda e: copy_to_clipboard(negative_text, "ネガティブプロンプト")
                        )
                    ]),
                    padding=ft.padding.only(top=0, bottom=0),
                    border=ft.border.only(
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                        bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                    ),
                )
            )
            metadata_text.controls.append(make_copyable_text(negative_text, size=11))
        #その他情報表示領域
        def other_textarea():
            metadata_text.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("その他情報", weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.COPY,
                            icon_size=14,
                            tooltip="その他情報をコピー",
                            on_click=lambda e: copy_to_clipboard(f"Steps: {other_info}", "その他情報")
                        )
                    ]),
                    padding=ft.padding.only(top=0, bottom=0),
                    border=ft.border.only(
                        top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                        bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                    ),
                )
            )
            metadata_text.controls.append(make_copyable_text(f"Steps: {other_info}", size=11))

        metadata_text.controls.clear()
        if not image_path:
            metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text("画像を選択してください", size=18)
            ])
            page.update()
            return
        try:
            stat = os.stat(image_path)
            size_kb = stat.st_size / 1024
            metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text("PNG メタデータ", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
            ])
            # メタデータ(tEXt / zTXt / iTXt)
            with open(image_path, "rb") as f:
                reader = png.Reader(file=f)
                for chunk_type, data in reader.chunks():
                    ctype = chunk_type.decode("latin1", errors="ignore")
                    if ctype == "tEXt":
                        text = data.decode("latin1", errors="ignore")
                        if "::" in text:
                            k, v = text.split("::", 1)
                            metadata_text.controls.append(ft.Text(f"{k}: {v}"))
                        else:
                            positive_index = text.find('parameters')
                            negative_index = text.find('Negative prompt: ')
                            anothers_index = text.find('Steps: ')
                            if positive_index != -1:
                                #Stable Diffusion WebUIで作られたもの
                                if negative_index == -1:
                                    # ネガプロがないもの(Fluxなど)
                                    prompt_text = text[positive_index+11:anothers_index].strip()
                                    other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                    # プロンプト
                                    prompt_textarea()
                                    # その他情報
                                    other_textarea()
                                else:
                                    #ネガプロがあるもの(IL系など)
                                    prompt_text = text[positive_index+11:negative_index].strip()
                                    negative_text = text[negative_index+17:anothers_index].strip()
                                    other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                    # プロンプト
                                    prompt_textarea()
                                    # ネガティブプロンプト
                                    negative_textarea()
                                    # その他情報
                                    other_textarea()
                            else:
                                #それ以外
                                metadata_text.controls.append(ft.Text(f"tEXt:\n{text}"))
                    elif ctype in ("iTXt", "zTXt"):
                        metadata_text.controls.append(ft.Text(f"{ctype}: あり"))
            # ファイル情報
            metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text(f"ファイル情報", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text(f"名前: {Path(image_path).name}"),
                ft.Text(f"サイズ: {size_kb:.1f} KB"),
                ft.Text(f"更新日時: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y/%m/%d %H:%M')}"),
            ])
            # IHDR(画像サイズなど)
            reader = png.Reader(filename=image_path)
            w, h, _, info = reader.read()
            metadata_text.controls.extend([
                ft.Text(f"幅 × 高さ: {w} × {h} px"),
                ft.Text(f"ビット深度: {info.get('bitdepth')}"),
                ft.Text(f"透明度: {'あり' if info.get('alpha') else 'なし'}"),
            ])
        except Exception as e:
            metadata_text.controls.append(ft.Text(f"エラー: {e}", color="red"))
        page.update()

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
    theme_colors = ThemeColors.dark() if settings['dark_theme'] else ThemeColors.light()

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
            ft.Divider(height=1),
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
    apply_theme()
    # 起動時にドライブ一覧表示
    show_drives()
#起動処理
ft.app(target=main)