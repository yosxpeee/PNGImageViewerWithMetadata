# pythonモジュール
import flet as ft
import io
from PIL import Image
import numpy as np
import struct
import win32clipboard

# 定数
BITMAPV5HEADER_SIZE = 124

####################
# テキストをクリップボードにコピー
####################
def copy_text_to_clipboard(page: ft.Page, text: str, name: str = "テキスト"):
    page.set_clipboard(text)
    snack = ft.SnackBar(
        content=ft.Text(f"{name}をコピーしました！"),
        bgcolor=ft.Colors.GREEN_700,
        duration=1500,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()

####################
# 画像をクリップボードにコピー（透明度あり/なし両対応）
####################
def copy_image_to_clipboard(page: ft.Page, image_path: str, alpha: bool):
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