import io
import struct
from PIL import Image
import numpy as np

BITMAPV5HEADER_SIZE = 124

####################
# PNG画像を透明度ありでコピーする
####################
def copy_pngdata_with_alpha(image_path):
    img = Image.open(image_path)
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
    img.close()
    return data
####################
# PNG画像を透明度なしでコピーする
####################
def copy_pngdata(image_path):
    img = Image.open(image_path)
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
    output.close()
    img.close()
    return data
