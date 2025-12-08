########################################
# center_panel.py
#
# 中央パネルの部品(人力でコード分割)
########################################
# pythonモジュール
import flet as ft
from pathlib import Path
from PIL import Image
import base64
import io
import asyncio
# 独自モジュール
import right_panel as rp

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
    # ローディングオーバーレイを取得
    loading_overlay = page.overlay[0] 
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
            # 10枚ごとに更新
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