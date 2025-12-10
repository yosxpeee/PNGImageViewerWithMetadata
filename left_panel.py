########################################
# left_panel.py
#
# 左パネルの部品(人力でコード分割)
########################################
# pythonモジュール
import flet as ft
import os
import string
from pathlib import Path
import win32api
# 独自モジュール
import center_panel as cp

####################
# 履歴のナビゲート
####################
def navigate_to(
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text, 
        theme_colors: dict, 
        dir_list: ft.ListView, 
        image_view: ft.Image,
        thumbnail_grid: ft.GridView,
        settings: dict,
    ):
    if page.history_index + 1 < len(page.navigation_history):
        page.navigation_history = page.navigation_history[:page.history_index + 1]
    page.navigation_history.append(path)
    page.history_index += 1
    refresh_directory(page, path, metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)

####################
# ディレクトリ情報更新
####################
def refresh_directory(
        page: ft.Page, 
        path: str, 
        metadata_text: ft.Column, 
        current_path_text: ft.Text, 
        theme_colors: dict, 
        dir_list: ft.ListView, 
        image_view: ft.Image,
        thumbnail_grid: ft.GridView,
        settings: dict,
    ):
    # ホバーエフェクト
    def rd_hover(e):
        back.bgcolor = theme_colors["selected"] if e.data == "true" else None
        back.update()

    dir_list.controls.clear()
    page.current_image_path = None
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
                    thumbnail_grid,
                    settings,
                    True
                ))
    # フォルダならサムネイルチェック
    if path != "<DRIVES>":
        p = Path(path)
        if p.is_dir():
            try:
                if any(item.suffix.lower() == ".png" for item in p.iterdir()):
                    # PNGがあれば非同期でサムネイル読み込み開始
                    page.run_task(
                        cp.show_thumbnails_async, 
                        page, path, current_path_text, image_view, thumbnail_grid, metadata_text, theme_colors, settings
                    )
                else:
                    # PNGなし
                    image_view.visible = False
                    thumbnail_grid.visible = False
                    metadata_text.controls.clear()
                    metadata_text.controls.extend([
                        ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                        ft.Text("このフォルダにPNG画像がありません", size=16),
                    ])
                    page.update()
            except PermissionError:
                metadata_text.controls.clear()
                metadata_text.controls.extend([
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                    ft.Text("このフォルダにPNG画像がありません", size=16),
                ])
                page.update()
    # ドライブ一覧ならサムネイル非表示
    else:
        image_view.visible = False
        thumbnail_grid.visible = False
        metadata_text.controls.clear()
        metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("画像を選択してください", size=18),
        ])
        page.update()
        return
    current_path_text.value = f"現在: {path}"
    p = Path(path)
    # ドライブ一覧に戻る
    back = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.COMPUTER, size=14),
            ft.Text("ドライブ一覧に戻る", expand=True, size=14),
            ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, opacity=0.5),
        ]),
        height=32,
        alignment=ft.alignment.top_center,
        padding=ft.padding.symmetric(horizontal=1, vertical=1),
        border_radius=8,
        ink=True,
        on_click=lambda e: navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings),
    )
    back.on_hover = rd_hover
    dir_list.controls.append(back)
    dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
    # 親フォルダ
    if p.parent != p:
        dir_list.controls.append(make_list_item(
            ".. (親フォルダ)", 
            ft.Icons.ARROW_BACK, 
            page, 
            str(p.parent), 
            metadata_text, 
            current_path_text, 
            theme_colors, 
            dir_list, 
            image_view, 
            thumbnail_grid, 
            settings, 
            True
        ))
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.is_dir():
                dir_list.controls.append(make_list_item(
                    item.name + "/", 
                    ft.Icons.FOLDER, 
                    page, str(item), 
                    metadata_text, 
                    current_path_text, 
                    theme_colors, 
                    dir_list, 
                    image_view, 
                    thumbnail_grid, 
                    settings, 
                    True
                ))
            elif item.suffix.lower() == ".png":
                dir_list.controls.append(make_list_item(
                    item.name, 
                    ft.Icons.IMAGE, 
                    page, 
                    str(item), 
                    metadata_text, 
                    current_path_text, 
                    theme_colors, 
                    dir_list, 
                    image_view, 
                    thumbnail_grid, 
                    settings, 
                False))
    except PermissionError:
        dir_list.controls.append(ft.Text("アクセス拒否", color="red"))
    page.update()
    # スクロール位置の復元(人力実装)
    for index, item in enumerate(page.scroll_position_history_left):
        if current_path_text.value in item:
            #print("見つかりました："+str(page.scroll_position_history_left[index]))
            info = page.scroll_position_history_left[index]
            if page.window.height == info[current_path_text.value]["window_height"]:
                # 高さが同じなら復元する
                dir_list.scroll_to(info[current_path_text.value]["scroll_pos"])
                page.update()
            else:
                # 高さが違うなら復元せず履歴削除(復元しない＝POS:0なので履歴不要)
                page.scroll_position_history_left.pop(index)

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
        dir_list: ft.ListView,
        image_view: ft.Image, 
        thumbnail_grid: ft.GridView,
        settings: dict,
        is_folder=False
    ):
    #クリック時のイベントハンドラ
    def on_click_handler(e):
        if path == "<DRIVES>":
            navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
        elif is_folder:
            navigate_to(page, path, metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
        else:
            cp.select_image(page, path, metadata_text, theme_colors, image_view, thumbnail_grid, settings)
    #ホバーエフェクト
    def mli_hover(e):
        container.bgcolor = theme_colors["hover"] if e.data == "true" else None
        container.update()

    container = ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=14),
            ft.Text(name, expand=True, size=14),
            ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, opacity=0.5),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        height=24,
        padding=ft.padding.symmetric(horizontal=1, vertical=1),
        border_radius=8,
        ink=True,
        on_click=on_click_handler,
    )
    container.on_hover = mli_hover
    return container