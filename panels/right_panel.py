########################################
# right_panel.py
#
# 右パネルの部品(人力でコード分割)
########################################
# pythonモジュール
import flet as ft
import os
import png
import zlib
from pathlib import Path
from datetime import datetime
# 独自モジュール
import clipboard
import themes

####################
# メタデータ表示の更新
####################
def update_metadata(
        image_path: str, 
        page: ft.Page, 
        metadata_text: ft.Column, 
        theme_colors:dict, 
        settings: dict
    ):
    # パーツ：コピペできるテキスト表示領域
    def make_copyable_text(value: str, size=12):
        return ft.TextField(
            value=value,
            read_only=True,
            multiline=True,
            border="none",
            text_size=size,
            min_lines=1,
            max_lines=100,
        )
    # プロンプト表示領域
    def prompt_textarea():
        metadata_text.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("プロンプト", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=14,
                        tooltip="プロンプトをコピー",
                        on_click=lambda e: clipboard.copy_text_to_clipboard(page, prompt_text, "プロンプト")
                    )
                ]),
                padding=ft.padding.only(top=0, bottom=0),
                border=ft.border.only(
                    top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                ),
            )
        )
        metadata_text.controls.append(make_copyable_text(prompt_text, size=13))
    # ネガティブプロンプト表示領域
    def negative_textarea():
        metadata_text.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("ネガティブプロンプト", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=14,
                        tooltip="ネガティブプロンプトをコピー",
                        on_click=lambda e: clipboard.copy_text_to_clipboard(page, negative_text, "ネガティブプロンプト")
                    )
                ]),
                padding=ft.padding.only(top=0, bottom=0),
                border=ft.border.only(
                    top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                ),
            )
        )
        metadata_text.controls.append(make_copyable_text(negative_text, size=13))
    #その他情報表示領域
    def other_textarea():
        metadata_text.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("その他情報", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=14,
                        tooltip="その他情報をコピー",
                        on_click=lambda e: clipboard.copy_text_to_clipboard(page, f"Steps: {other_info}", "その他情報")
                    )
                ]),
                padding=ft.padding.only(top=0, bottom=0),
                border=ft.border.only(
                    top=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE))
                ),
            )
        )
        metadata_text.controls.append(make_copyable_text(f"Steps: {other_info}", size=13))
    metadata_text.controls.clear()
    if not image_path:
        metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("画像を選択してください", size=18)
        ])
        page.update()
        return
    try:
        stat = os.stat(image_path)
        size_kb = stat.st_size / 1024
        theme_colors = themes.ThemeColors.dark() if settings["dark_theme"] else themes.ThemeColors.light()
        metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("PNG メタデータ", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
        ])
        # メタデータ(tEXt / zTXt / iTXt)
        with open(image_path, "rb") as f:
            reader = png.Reader(file=f)
            for chunk_type, data in reader.chunks():
                ctype = chunk_type.decode("latin1", errors="ignore")
                if ctype == "tEXt":
                    text = data.decode("latin1", errors="ignore")
                    if "::" in text:
                        k, v = text.split("::", 1)
                        metadata_text.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
                        metadata_text.controls.append(ft.Text(f"{ctype}: ", weight=ft.FontWeight.BOLD))
                        metadata_text.controls.append(ft.Text(f"{k}: {v}"))
                    else:
                        positive_index = text.find('parameters')
                        negative_index = text.find('Negative prompt: ')
                        anothers_index = text.find('Steps: ')
                        if positive_index != -1:
                            #Stable Diffusion WebUIで作られたもの
                            if negative_index == -1:
                                # ネガプロがないもの(Fluxなど)
                                prompt_text = text[positive_index+11:anothers_index].strip()
                                other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                # プロンプト
                                prompt_textarea()
                                # その他情報
                                other_textarea()
                            else:
                                #ネガプロがあるもの(IL系など)
                                prompt_text = text[positive_index+11:negative_index].strip()
                                negative_text = text[negative_index+17:anothers_index].strip()
                                other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                # プロンプト
                                prompt_textarea()
                                # ネガティブプロンプト
                                negative_textarea()
                                # その他情報
                                other_textarea()
                        else:
                            #それ以外
                            metadata_text.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
                            metadata_text.controls.append(ft.Text(f"{ctype}: ", weight=ft.FontWeight.BOLD))
                            metadata_text.controls.append(ft.Text(f"{text}"))
                elif ctype == "zTXt":
                    metadata_text.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
                    metadata_text.controls.append(ft.Text(f"{ctype}: ", weight=ft.FontWeight.BOLD))
                    try:
                        keyword_end = data.index(b"\0")
                        keyword = data[:keyword_end].decode("latin1")
                        compressed = data[keyword_end+2:]  # +1 for null, +1 for compression method
                        decompressed = zlib.decompress(compressed)
                        text = decompressed.decode("utf-8", errors="replace")
                        metadata_text.controls.append(ft.Text(f"{keyword}: {text}"))
                    except Exception as e:
                        metadata_text.controls.append(ft.Text(f"デコード失敗({e})", color=ft.Colors.RED))
                elif ctype == "iTXt":
                    metadata_text.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
                    metadata_text.controls.append(ft.Text(f"{ctype}: ", weight=ft.FontWeight.BOLD))
                    try:
                        null1 = data.index(b"\0")
                        keyword = data[:null1].decode("latin1")
                        compression_flag = data[null1+1]
                        compression_method = data[null1+2]
                        lang_tag_end = data.index(b"\0", null1+3)
                        lang_tag = data[null1+3:lang_tag_end].decode("utf-8", errors="ignore")
                        translated_keyword_end = data.index(b"\0", lang_tag_end+1)
                        translated_keyword = data[lang_tag_end+1:translated_keyword_end].decode("utf-8", errors="replace")
                        text_data = data[translated_keyword_end+1:]
                        if compression_flag == 1:  # 圧縮されている（zlib）
                            if compression_method != 0:
                                text = f"不明な圧縮方式"
                            else:
                                text = zlib.decompress(text_data).decode("utf-8", errors="replace")
                        else:
                            text = text_data.decode("utf-8", errors="replace")
                        if lang_tag != "":
                            metadata_text.controls.append(ft.Text(f"language tag: {lang_tag}"))
                        if translated_keyword != "":
                            metadata_text.controls.append(ft.Text(f"translated keyword: {translated_keyword}"))
                        metadata_text.controls.append(ft.Text(f"{keyword}: {text}"))
                    except Exception as e:
                        metadata_text.controls.append(ft.Text(f"デコード失敗({e})", color=ft.Colors.RED))
        # ファイル情報
        metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text(f"ファイル情報", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text(f"名前: {Path(image_path).name}"),
            ft.Text(f"サイズ: {size_kb:.1f} KB"),
            ft.Text(f"更新日時: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y/%m/%d %H:%M')}"),
        ])
        # IHDR(画像サイズなど)
        reader = png.Reader(filename=image_path)
        w, h, _, info = reader.read()
        metadata_text.controls.extend([
            ft.Text(f"幅 × 高さ: {w} × {h} px"),
            ft.Text(f"ビット深度: {info.get('bitdepth')}"),
            ft.Text(f"透明度: {'あり' if info.get('alpha') else 'なし'}"),
        ])
    except Exception as e:
        metadata_text.controls.append(ft.Text(f"エラー: {e}", color="red"))
    page.update()