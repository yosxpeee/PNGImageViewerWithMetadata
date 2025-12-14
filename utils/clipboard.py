import flet as ft
import io
from PIL import Image
import numpy as np
import struct
import win32clipboard

BITMAPV5HEADER_SIZE = 124

####################
# テキストをクリップボードにコピー
####################
def copy_text_to_clipboard(page: ft.Page, text: str, name: str = "テキスト"):
    page.set_clipboard(text)
    snack = ft.SnackBar(
        content=ft.Text(f"{name}をコピーしました！", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.GREEN_700,
        duration=1500,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()
####################
# 画像をクリップボードにコピー
####################
def copy_image_to_clipboard(page: ft.Page, image_path: str, alpha: bool):
    try:
        img = Image.open(image_path)
        if alpha:
            img = img.convert("RGBA")
            w, h = img.size
            arr = np.array(img)
            bgra = arr[:, :, [2, 1, 0, 3]]
            pixels = np.flipud(bgra).tobytes()
            header = struct.pack(
                "<LllHHLLllLLllllLLllllLLLlLLLLLLLLL",
                BITMAPV5HEADER_SIZE, w, h, 1, 32, 3, 0, 0, 0, 0, 0, 0,
                0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000,
                0x73524742, 0,0,0,0,0,0,0,0,0, 0,0,0, 0, 0,0,0,0
            )
            data = header + pixels
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIBV5, data)
            done_msg = "(透明度あり)"
        else:
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
            data = output.getvalue()[14:]
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            done_msg = "(透明度なし)"
            output.close()
        # PNGも登録
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_format = win32clipboard.RegisterClipboardFormat("PNG")
        if png_format:
            win32clipboard.SetClipboardData(png_format, buf.getvalue())
        win32clipboard.CloseClipboard()
        snack = ft.SnackBar(
            content=ft.Text("画像をクリップボードにコピーしました！" + done_msg, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_700,
            duration=1500,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        snack = ft.SnackBar(
            content=ft.Text(f"コピー失敗: {e}", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_700,
            duration=1500,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()