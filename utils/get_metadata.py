import zlib

####################
# tEXt取得
#
# 画像がStable Diffusion WebUIで作られているかどうかはparametersがあるかどうかで判断
# Stable Diffusion WebUIで作られたもの
#   text          = 空文字
#   prompt_text   = ポジティブプロンプト
#   negative_text = ネガティブプロンプト(空の場合あり)
#   other_info    = その他情報
# それ以外
#   text          = メタデータそのまま
#   prompt_text   = 空文字
#   negative_text = 空文字
#   other_info    = 空文字
####################
def get_tEXt(data):
    text = ""
    prompt_text = ""
    negative_text = ""
    other_info = ""
    text_raw = data.decode("latin1", errors="ignore")
    if "::" in text_raw:
        k, v = text_raw.split("::", 1)
        text = f"tEXt: {k}: {v}"
    else:
        positive_index = text_raw.find('parameters')
        negative_index = text_raw.find('Negative prompt: ')
        others_index   = text_raw.find('Steps: ')
        if positive_index == -1 and (negative_index != -1 or others_index != -1):
            # parametersが見つからないが、Negative prompt: または Steps: が見つかった場合、
            # Stable Diffusion WebUI由来と判断して先頭にparametersを追加する
            # (e.g. Stealth PNG Infoの場合)
            text_raw = "parameters " + text_raw
            positive_index = 0
            if (negative_index != -1):
                negative_index += 11
            others_index += 11
        if positive_index != -1:
            if negative_index == -1:
                prompt_text = text_raw[positive_index+11:others_index].strip()
                other_info = text_raw[others_index+7:].strip().replace(", ", "\n")
            else:
                prompt_text = text_raw[positive_index+11:negative_index].strip()
                negative_text = text_raw[negative_index+17:others_index].strip()
                other_info = text_raw[others_index+7:].strip().replace(", ", "\n")
        else:
            text = f"tEXt: {text_raw}"
    return text, prompt_text, negative_text, other_info
####################
# zTXt取得
####################
def get_zTxt(data):
    keyword_end = data.index(b"\0")
    keyword = data[:keyword_end].decode("latin1")
    compressed = data[keyword_end+2:]
    decompressed = zlib.decompress(compressed)
    text = decompressed.decode("utf-8", errors="replace")
    text = f"{keyword}: {text}"
    return text
####################
# iTXt取得
####################
def get_iTXt(data):
    text = ""
    exception = ""
    null1 = data.index(b"\0")
    keyword = data[:null1].decode("latin1")
    compression_flag = data[null1+1]
    compression_method = data[null1+2]
    lang_tag_end = data.index(b"\0", null1+3)
    lang_tag = data[null1+3:lang_tag_end].decode("utf-8", errors="ignore")
    translated_keyword_end = data.index(b"\0", lang_tag_end+1)
    translated_keyword = data[lang_tag_end+1:translated_keyword_end].decode("utf-8", errors="replace")
    text_data = data[translated_keyword_end+1:]
    if compression_flag == 1:
        if compression_method != 0:
            text = f"不明な圧縮方式"
            return text, exception
        else:
            text_raw = zlib.decompress(text_data).decode("utf-8", errors="replace")
    else:
        text_raw = text_data.decode("utf-8", errors="replace")
    if lang_tag != "":
        text += f"language tag: {lang_tag}\n"
    if translated_keyword != "":
        text += f"translated keyword: {translated_keyword}\n"
    text += f"{keyword}: {text_raw}"
    return text