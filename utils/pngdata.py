import io
import struct
import gzip
import zlib
import numpy as np
from PIL import Image

BITMAPV5HEADER_SIZE = 124

####################
# PNG画像を透明度ありでコピーする
####################
def copy_pngdata_with_alpha(img):
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
    return data
####################
# PNG画像を透明度なしでコピーする
####################
def copy_pngdata(img):
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
    return data
####################
# PNG画像からステルスデータを検出する
# (ここだけGPT-5 miniによる生成コード)
####################
def detect_stealth_from_image(path):
    pil_img = Image.open(path).convert("RGBA")
    arr = np.array(pil_img)
    h, w = arr.shape[0], arr.shape[1]
    bit_stream_a = []
    bit_stream_rgb = []
    for x in range(w):
        for y in range(h):
            r, g, b, a = arr[y, x]
            bit_stream_rgb.append(str(int(r) & 1))
            bit_stream_rgb.append(str(int(g) & 1))
            bit_stream_rgb.append(str(int(b) & 1))
            bit_stream_a.append(str(int(a) & 1))
    candidates = [''.join(bit_stream_a), ''.join(bit_stream_rgb)]
    signatures = { 'stealth_pnginfo': { 'mode': 'Alpha', 'compressed': False },
                   'stealth_pngcomp': { 'mode': 'Alpha', 'compressed': True },
                   'stealth_rgbinfo': { 'mode': 'RGB', 'compressed': False },
                   'stealth_rgbcomp': { 'mode': 'RGB', 'compressed': True } }
    def binary_to_text(binstr):
        try:
            b = bytearray()
            for i in range(0, len(binstr), 8):
                chunk = binstr[i:i+8]
                if len(chunk) == 8:
                    b.append(int(chunk, 2))
            return bytes(b).decode('utf-8', errors='ignore')
        except Exception:
            return ''
    for idx, bit_string in enumerate(candidates):
        for sig_text, siginfo in signatures.items():
            sig_bits = ''.join(format(ord(c), '08b') for c in sig_text)
            sig_len = len(sig_bits)
            if len(bit_string) < sig_len + 32:
                continue
            sig_binary = bit_string[:sig_len]
            parsed = binary_to_text(sig_binary)
            if parsed != sig_text:
                continue
            current_stream = bit_string[sig_len:]
            len_binary = current_stream[:32]
            try:
                param_len_bits = int(len_binary, 2)
            except Exception:
                continue
            current_stream = current_stream[32:]
            if len(current_stream) < param_len_bits:
                continue
            binary_data = current_stream[:param_len_bits]
            # ビット列からバイト列への変換
            param_bytes = bytearray()
            for i in range(0, len(binary_data), 8):
                byte_str = binary_data[i:i+8]
                if len(byte_str) == 8:
                    param_bytes.append(int(byte_str, 2))
            param_bytes = bytes(param_bytes)
            try:
                if siginfo['compressed']:
                    # 圧縮されていたら展開
                    try:
                        param_text = zlib.decompress(param_bytes).decode('utf-8', errors='ignore')
                    except Exception:
                        param_text = gzip.decompress(param_bytes).decode('utf-8', errors='ignore')
                else:
                    param_text = param_bytes.decode('utf-8', errors='ignore')
                return {
                    'signature': sig_text,
                    'candidate_index': idx,
                    'length_bits': param_len_bits,
                    'text': param_text,
                }
            except Exception:
                continue
    return None