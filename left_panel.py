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
import asyncio

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
    # フォルダならサムネイルチェック
    if path != "<DRIVES>":
        p = Path(path)
        if p.is_dir():
            if any(item.suffix.lower() == ".png" for item in p.iterdir()):
                # PNGがあれば非同期でサムネイル読み込み開始！
                page.run_task(
                    show_thumbnails_async, 
                    page, path, image_view, thumbnail_grid, metadata_text, theme_colors, settings
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
async def show_thumbnails_async(
        page: ft.Page,
        folder_path: str,
        image_view: ft.Image,
        thumbnail_grid: ft.GridView,
        metadata_text: ft.Column,
        theme_colors: dict,
        settings: dict
    ):
    # ローディングオーバーレイを正しく取得（page.overlay[0] が確実体）
    loading_overlay = page.overlay[0]  # ← これで確実に取れる！
    loading_overlay.visible = True
    loading_overlay.content.controls[1].value = "読み込み中…"
    page.update()

    # 既存サムネイルクリア
    thumbnail_grid.controls.clear()
    try:
        png_files = [p for p in Path(folder_path).iterdir() if p.suffix.lower() == ".png"]
        png_files = sorted(png_files, key=lambda x: x.name.lower())
    except Exception as e:
        loading_overlay.visible = False
        metadata_text.controls.clear()
        metadata_text.controls.append(ft.Text(f"フォルダ読み込みエラー: {e}", color="red"))
        page.update()
        return
    if not png_files:
        loading_overlay.visible = False
        image_view.visible = False
        thumbnail_grid.visible = False
        metadata_text.controls.clear()
        metadata_text.controls.extend([
            ft.Divider(height=1),
            ft.Text("このフォルダにPNG画像がありません", size=16),
        ])
        page.update()
        return
    # グリッド表示開始
    image_view.visible = False
    thumbnail_grid.visible = True
    for i, png_path in enumerate(png_files):
        # 別のフォルダに移動されたら即キャンセル
        if page.navigation_history[page.history_index] != folder_path:
            loading_overlay.visible = False
            page.update()
            return
        try:
            with Image.open(png_path) as img:
                img.thumbnail((160, 160))
                byte_io = io.BytesIO()
                img.save(byte_io, format="PNG")
                base64_str = base64.b64encode(byte_io.getvalue()).decode()
            container = ft.Container(
                width=160, height=160,
                border_radius=12,
                padding=6,
                bgcolor=ft.Colors.GREY, #灰色固定にする
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, "#000000")),
                animate_scale=ft.Animation(300, "ease_out_back"),
                scale=1.0,
                content=ft.Image(src_base64=base64_str, fit=ft.ImageFit.CONTAIN),
                tooltip=png_path.name,
            )
            # ホバーで拡大
            container.on_hover = lambda e, c=container: (
                setattr(c, "scale", 1.12 if e.data == "true" else 1.0) or c.update()
            )
            # クリックで画像表示
            container.on_click = lambda e, p=str(png_path): (
                setattr(page, "current_image_path", p),
                select_image(page, p, metadata_text, theme_colors, image_view, thumbnail_grid, settings)
            )
            thumbnail_grid.controls.append(container)
            # 10枚ごとに更新（ヌルヌル表示！）
            if i % 10 == 0 or i == len(png_files) - 1:
                percent = int((i + 1) / len(png_files) * 100)
                loading_overlay.content.controls[1].value = f"読み込み中… {i+1}/{len(png_files)} ({percent}%)"
                page.update()
                await asyncio.sleep(0.01) # 標準のasyncioを使う
        except Exception as e:
            print(f"サムネイル生成失敗 {png_path}: {e}")
            # エラーでもグリッドには表示しない（スキップ）
    # 読み込み完了！
    loading_overlay.visible = False
    metadata_text.controls.clear()
    metadata_text.controls.extend([
        ft.Divider(height=1),
        ft.Text(f"サムネイルビュー: {len(thumbnail_grid.controls)} 枚", size=16, weight=ft.FontWeight.BOLD),
        ft.Text(folder_path, size=12, color=ft.Colors.OUTLINE),
    ])
    page.update()