########################################
# image_viewer.py
#
# 根幹は Grok 4.1 beta に作らせてみました。
########################################
import flet as ft
import os
from pathlib import Path
import string
import png
from datetime import datetime
import threading
import time
import win32api # type: ignore
import win32con # type: ignore

####################
# メイン関数
####################
def main(page: ft.Page):
    ####################
    # 各種イベント処理
    ####################
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
    # イベント処理：履歴のナビゲート
    def navigate_to(path: str):
        if page.history_index + 1 < len(page.navigation_history):
            page.navigation_history = page.navigation_history[:page.history_index + 1]
        
        page.navigation_history.append(path)
        page.history_index += 1
        refresh_directory(path)
    # イベント処理：マウス
    def on_mouse_event(e: ft.MouseEvent):
        print(e.button)
        if e.button == ft.MouseButton.BACK:
            print("戻る")
            go_back()
        elif e.button == ft.MouseButton.FORWARD:
            print("進む")
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

    ####################
    # 右ペインの処理
    ####################
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
                ft.Text("PNG メタデータ", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.TEAL_900),
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
                ft.Text("ファイル情報", weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.TEAL_900),
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
            container.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE) if e.data == "true" else None
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
            back.bgcolor = ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY) if e.data == "true" else None
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
    # 主処理開始
    ####################
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
    page.on_mouse_event = on_mouse_event   # マウスイベントの指定

    # 起動時にイベントリスナー開始
    start_mouse_back_forward_listener()

    # ── 左ペイン：ファイルブラウザ ──
    current_path_text = ft.Text("", size=12, italic=False, color=ft.Colors.OUTLINE)
    dir_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    show_drives() # 起動時にドライブ一覧表示
    # ── 中央：画像表示 ──
    image_view = ft.Image(
        src="", 
        fit=ft.ImageFit.CONTAIN, 
        expand=True
    )
    # ── 右ペイン：メタデータ ──
    metadata_text = ft.Column([
        ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
        ft.Text("画像を選択してください", size=18),
        ], scroll=ft.ScrollMode.AUTO, expand=True
    )

    # ── 最終レイアウト(サイドパネル：白)──
    page.add(
        ft.Row([
            # 左：白背景(ファイルブラウザ)
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.EXPLORE), ft.Text("ファイルブラウザ", weight=ft.FontWeight.BOLD)]),
                    current_path_text,
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                    dir_list,
                ], expand=True),
                bgcolor=ft.Colors.WHITE,
                padding=10,
                width=340,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            ),
            # 中央：画像
            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
            ft.Container(image_view, alignment=ft.alignment.center, expand=2),
            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),
            # 右：白背景(メタデータ)
            ft.Container(
                content=ft.Column([
                    ft.Text("画像情報", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLUE_ACCENT_200),
                    metadata_text,
                ], expand=True),
                bgcolor=ft.Colors.WHITE,
                padding=15,
                width=400,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            ),
        ], expand=True)
    )

#起動処理
ft.app(target=main)