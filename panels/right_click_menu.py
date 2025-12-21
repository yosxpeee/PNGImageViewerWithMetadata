import flet as ft
import io
import os
import win32clipboard
import struct
import numpy as np
from pathlib import Path
from PIL import Image

from utils.pngdata import copy_pngdata_with_alpha, copy_pngdata

####################
# テキストをクリップボードにコピー
####################
def copy_text_to_clipboard(page: ft.Page, text: str, name: str = "テキスト"):
    page.set_clipboard(text)
    page.open(ft.SnackBar(
        content=ft.Text(f"{name}をコピーしました！", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_700,
        duration=1500,
    ))
####################
# 画像をクリップボードにコピー
####################
def copy_image_to_clipboard(page: ft.Page, image_path: str, alpha: bool):
    try:
        with Image.open(image_path) as img:
            if alpha:
                data = copy_pngdata_with_alpha(img)
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIBV5, data)
                #オリジナルのPNGも追加登録
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_format = win32clipboard.RegisterClipboardFormat("PNG")
                if png_format:
                    win32clipboard.SetClipboardData(png_format, buf.getvalue())
                msg = "あり"
            else:
                data = copy_pngdata(img)
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                msg = "なし"
            win32clipboard.CloseClipboard()
            page.overlay.pop(),
            page.open(ft.SnackBar(
                content=ft.Text(f"画像をクリップボードにコピーしました！(透明度{msg})" ,color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                duration=1500,
            ))
        page.update()
    except Exception as e:
        page.open(ft.SnackBar(
            content=ft.Text(f"コピー失敗: {e}", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700,
            duration=1500,
        ))
        page.update
####################
# メタデータなしで所定の場所に保存する
####################
def save_without_metadata(page: ft.Page, image_path: str):
    try:
        with Image.open(image_path) as img:
            data = copy_pngdata_with_alpha(img)
            # output ディレクトリを確保
            script_dir = Path(__import__("__main__").__file__).parent.resolve()
            output_dir = script_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            # 保存パス
            original_path = Path(image_path)
            new_filename = original_path.stem + "_cleaned" + original_path.suffix
            save_path = output_dir / new_filename
            # 元画像からサイズ取得
            w, h = img.size
            # ヘッダーサイズをdata自身から正しく読み取る（BITMAPINFOHEADERの先頭4バイト）
            header_size = struct.unpack("<I", data[0:4])[0]
            pixel_data = data[header_size:]
            # パディングを考慮した正しい行サイズ（4バイトアライメント）
            bytes_per_pixel = 4
            padded_row_size = ((w * bytes_per_pixel + 3) // 4) * 4
            expected_size = padded_row_size * h
            # 実際のサイズと比較
            actual_size = len(pixel_data)
            if actual_size != expected_size:
                # 強制的に正しいサイズに切り詰める
                if actual_size == expected_size + 8 and header_size == 124:
                    pixel_data = pixel_data[:-8]
                else:
                    raise ValueError(f"ピクセルデータサイズ不一致: {actual_size} != {expected_size}")
            # NumPyでreshape
            arr = np.frombuffer(pixel_data, dtype=np.uint8).reshape((h, padded_row_size))
            # パディング部分を削除して (h, w, 4) に
            arr = arr[:, :w * 4].reshape((h, w, 4))
            # BGRA → RGBA
            arr = arr[:, :, [2, 1, 0, 3]]
            # BITMAPは下から始まるので反転
            arr = np.flipud(arr)
            # 画像作成＆保存
            clean_img = Image.fromarray(arr, mode="RGBA")
            clean_img.save(save_path, format="PNG")
            # outputディレクトリで作業していた場合のコーナーケース対応
            # (サムネイル表示に戻ってしまうが致し方なし、コーナーケースなので許容する)
            if os.path.dirname(page.current_image_path) == os.path.dirname(str(save_path)):
                from panels.left_panel import LeftPanel
                LeftPanel.instance.refresh_directory(os.path.dirname(image_path))
        page.overlay.pop(),
        page.open(ft.SnackBar(
            content=ft.Text(f"画像をメタデータなしで保存しました！ [{str(save_path)}]" ,color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_700,
            duration=1500,
        ))
        page.update()
    except Exception as e:
        page.open(ft.SnackBar(
            content=ft.Text(f"ファイル保存失敗: {e}", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700,
            duration=1500,
        ))
        page.update()
####################
# 右クリックメニューの作成
####################
def create_image_context_menu(page: ft.Page, menu_x, menu_y, current_path):
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
                title=ft.Text("画像をクリップボードにコピー\n(透明度あり)", size=12),
                on_click=lambda e: copy_image_to_clipboard(page, current_path, True)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.COPY, size=18),
                title=ft.Text("画像をクリップボードにコピー\n(透明度なし)", size=12),
                on_click=lambda e: copy_image_to_clipboard(page, current_path, False)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SAVE, size=18),
                title=ft.Text("メタデータを消去して保存する", size=12),
                on_click=lambda e: save_without_metadata(page, current_path)
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.FOLDER_OPEN, size=18),
                title=ft.Text("この画像の保存ディレクトリを\nエクスプローラーで開く", size=12),
                on_click=lambda e: (
                    __import__("subprocess").Popen(f'explorer /select,"{current_path}"'),
                    page.overlay.pop(),
                    page.update()
                ),
            ),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CLOSE, size=18),
                title=ft.Text("キャンセル", size=12, color=ft.Colors.ERROR),
                on_click=lambda e: (
                    page.overlay.pop(),
                    page.update()
                ),
            ),
        ], spacing=0),
    )
    overlay = ft.Stack([
        ft.Container(bgcolor=ft.Colors.TRANSPARENT, on_click=lambda e: (page.overlay.pop(), page.update()), expand=True),
        ft.Container(content=context_menu, top=menu_y - 100, left=menu_x - 120, animate=ft.Animation(150, "decelerate")),
    ], expand=True)
    page.overlay.append(overlay)
    page.update()