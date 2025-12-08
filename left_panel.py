# pythonモジュール
import flet as ft
import os
import string
from pathlib import Path
import win32api
# 独自モジュール
import right_panel as rp

####################
# 履歴のナビゲート
####################
def navigate_to(
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text, 
        theme_colors: dict, 
        dir_list: ft.Column, 
        image_view: ft.Image,
        settings: dict,
    ):
    if page.history_index + 1 < len(page.navigation_history):
        page.navigation_history = page.navigation_history[:page.history_index + 1]
    page.navigation_history.append(path)
    page.history_index += 1
    refresh_directory(page, path, metadata_text, current_path_text, theme_colors, dir_list, image_view, settings)

####################
# ディレクトリ情報更新
####################
def refresh_directory(
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text, 
        theme_colors: dict, 
        dir_list: ft.Column, 
        image_view: ft.Image,
        settings: dict,
    ):
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
                dir_list.controls.append(make_list_item(
                    f"{drive} [{label}]", 
                    ft.Icons.STORAGE, 
                    page, 
                    drive, 
                    metadata_text,
                    current_path_text, 
                    theme_colors, 
                    dir_list, 
                    image_view, 
                    settings,
                    True
                ))
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
        on_click=lambda e: navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view),
    )
    back.on_hover = rd_hover
    dir_list.controls.append(back)
    dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),)
    # 親フォルダ
    if p.parent != p:
        dir_list.controls.append(make_list_item(".. (親フォルダ)", ft.Icons.ARROW_BACK, page, str(p.parent), metadata_text, current_path_text, theme_colors, dir_list, image_view, settings, True))
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.is_dir():
                dir_list.controls.append(make_list_item(item.name + "/", ft.Icons.FOLDER, page, str(item), metadata_text, current_path_text, theme_colors, dir_list, image_view, settings, True))
            elif item.suffix.lower() == ".png":
                dir_list.controls.append(make_list_item(item.name, ft.Icons.IMAGE, page, str(item), metadata_text, current_path_text, theme_colors, dir_list, image_view, settings, False))
    except PermissionError:
        dir_list.controls.append(ft.Text("アクセス拒否", color="red"))
    page.update()

####################
# 高さ調整可能＆ホバーエフェクトの汎用アイテム生成
####################
def make_list_item(
        name: str, 
        icon: ft.Icon, 
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text,
        theme_colors: dict, 
        dir_list: ft.Column,
        image_view: ft.Image, 
        settings: dict,
        is_folder=False
    ):
    #クリック時のイベントハンドラ
    def on_click_handler(e):
        if path == "<DRIVES>":
            show_drives(page, metadata_text, current_path_text, theme_colors, dir_list, image_view, settings)
        elif is_folder:
            navigate_to(page, path, metadata_text, current_path_text, theme_colors, dir_list, image_view, settings)
        else:
            select_image(page, path, metadata_text, theme_colors, image_view, settings)
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

####################
# 画像選択
####################
def select_image(
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        theme_colors: dict, 
        image_view: ft.Image, 
        settings: dict
    ):
    image_view.src = path
    rp.update_metadata(path, page, metadata_text, theme_colors, settings)
    page.update()

####################
# ドライブ一覧表示
####################
def show_drives(
        page: ft.Page, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text, 
        theme_colors: dict, 
        dir_list: dict, 
        image_view: ft.Image, 
        settings: dict
    ):
    navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view, settings)