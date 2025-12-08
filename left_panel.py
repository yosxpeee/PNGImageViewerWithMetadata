# pythonモジュール
import flet as ft
import os
import string
from pathlib import Path
import win32api
from PIL import Image
import base64
import io
# 独自モジュール
import right_panel as rp
import themes

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
        dir_list: ft.Column, 
        image_view: ft.Image,
        thumbnail_grid: ft.GridView,
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
                    thumbnail_grid,
                    settings,
                    True
                ))

    # 最後に、フォルダならサムネイルチェック
    if path != "<DRIVES>":
        p = Path(path)
        if p.is_dir():
            # PNGがあるかチェックしてサムネイル表示
            if any(item.suffix.lower() == ".png" for item in p.iterdir()):
                show_thumbnails(page, path, image_view, thumbnail_grid, metadata_text, theme_colors, settings)
            else:
                # PNGなし → 単体ビュー待機状態
                image_view.visible = False
                thumbnail_grid.visible = False
                metadata_text.controls.clear()
                metadata_text.controls.extend([
                    ft.Divider(height=1),
                    ft.Text("このフォルダにPNG画像がありません", size=16),
                ])
                page.update()
    # ドライブ一覧ならサムネイル非表示
    else:
        image_view.visible = False
        thumbnail_grid.visible = False

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
        on_click=lambda e: navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings),
    )
    back.on_hover = rd_hover
    dir_list.controls.append(back)
    dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),)
    # 親フォルダ
    if p.parent != p:
        dir_list.controls.append(make_list_item(".. (親フォルダ)", ft.Icons.ARROW_BACK, page, str(p.parent), metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings, True))
    try:
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.is_dir():
                dir_list.controls.append(make_list_item(item.name + "/", ft.Icons.FOLDER, page, str(item), metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings, True))
            elif item.suffix.lower() == ".png":
                dir_list.controls.append(make_list_item(item.name, ft.Icons.IMAGE, page, str(item), metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings, False))
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
        thumbnail_grid: ft.GridView,
        settings: dict,
        is_folder=False
    ):
    #クリック時のイベントハンドラ
    def on_click_handler(e):
        if path == "<DRIVES>":
            show_drives(page, metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
        elif is_folder:
            navigate_to(page, path, metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)
        else:
            select_image(page, path, metadata_text, theme_colors, image_view, thumbnail_grid, settings)
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
        thumbnail_grid: ft.GridView,
        settings: dict
    ):
    image_view.src = path
    image_view.visible = True
    thumbnail_grid.visible = False  # グリッドを隠す
    page.current_image_path = path
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
        thumbnail_grid: ft.GridView,
        settings: dict
    ):
    navigate_to(page, "<DRIVES>", metadata_text, current_path_text, theme_colors, dir_list, image_view, thumbnail_grid, settings)

####################
# サムネイルグリッド表示
####################
def show_thumbnails(
    page: ft.Page,
    folder_path: str,
    image_view: ft.Image,
    thumbnail_grid: ft.GridView,
    metadata_text: ft.Column,
    theme_colors: dict,
    settings: dict
):
    thumbnail_grid.controls.clear()
    png_files = [p for p in Path(folder_path).iterdir() if p.suffix.lower() == ".png"]
    
    if not png_files:
        # PNGがなければ単体ビューに戻してメッセージ表示
        image_view.visible = False
        thumbnail_grid.visible = False
        metadata_text.controls.clear()
        metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("画像を選択してください", size=18),
        ])
        page.update()
        return

    # PNGがあればグリッド表示
    image_view.visible = False
    thumbnail_grid.visible = True

    for png_path in sorted(png_files, key=lambda x: x.name.lower()):
        try:
            with Image.open(png_path) as img:
                img.thumbnail((160, 160))
                byte_io = io.BytesIO()
                img.save(byte_io, format="PNG")
                img_data = byte_io.getvalue()

            # Base64エンコード
            base64_str = base64.b64encode(img_data).decode()

            # ここが大事！ImageをContainerで包んで装飾
            thumbnail_image = ft.Image(
                src_base64=base64_str,
                fit=ft.ImageFit.CONTAIN,
                width=160,
                height=160,
            )
            thumbnail_container = ft.Container(
                content=thumbnail_image,
                width=160,
                height=160,
                border_radius=10,
                bgcolor=ft.Colors.GREY, #あえて固定にする
                padding=4,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                    offset=ft.Offset(0, 4),
                ),
                alignment=ft.alignment.center,
                on_click=lambda e, p=str(png_path): (
                    setattr(page, "current_image_path", p),
                    select_image(page, p, metadata_text, theme_colors, image_view, thumbnail_grid, settings)
                ),
                tooltip=png_path.name,
                # ホバーでちょっと浮かす演出
                animate_scale=ft.Animation(200, "ease_out"),
                scale=1.0,
                on_hover=lambda e: (
                    setattr(e.control, "scale", 1.08 if e.data == "true" else 1.0),
                    e.control.update()
                )
            )

            thumbnail_grid.controls.append(thumbnail_container)

        except Exception as e:
            print(f"サムネイル生成エラー {png_path}: {e}")
            # エラー時もプレースホルダー表示
            thumbnail_grid.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR, size=40, color=ft.Colors.RED_400),
                        ft.Text(png_path.name, size=10, no_wrap=True, text_align="center")
                    ], horizontal_alignment="center", spacing=4),
                    width=160,
                    height=160,
                    bgcolor=theme_colors["bg_panel"],
                    border_radius=10,
                )
            )

    # メタデータはクリア（サムネイルモードでは非表示）
    metadata_text.controls.clear()
    metadata_text.controls.extend([
        ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
        ft.Text(f"サムネイルビュー: {len(png_files)} 枚", size=16, weight=ft.FontWeight.BOLD),
        ft.Text(folder_path, size=12, color=ft.Colors.OUTLINE),
    ])
    page.update()