import flet as ft
import os
import png
import zlib
from pathlib import Path
from datetime import datetime

from utils.clipboard import copy_text_to_clipboard

class RightPanel:
    instance = None
    # 初期化
    def __init__(self, page, settings, theme_manager):
        self.page = page
        self.settings = settings
        self.theme_manager = theme_manager
        RightPanel.instance = self
        self.metadata_text = ft.Column(
            scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.container = ft.Container(
            content=ft.Column([
                ft.Text("画像情報", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.BLUE_ACCENT_200),
                self.metadata_text,
            ], expand=True),
            padding=15,
            width=400,
            bgcolor=theme_manager.colors["bg_panel"],
        )
    ####################
    # 画像非選択のときの画面
    ####################
    def update_no_selection(self):
        self.metadata_text.controls.clear()
        self.metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("画像を選択してください", size=18),
        ])
        self.page.update()
    ####################
    # 画像が存在しないときの画面
    def update_no_images(self):
        self.metadata_text.controls.clear()
        self.metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("このフォルダにPNG画像がありません", size=16),
        ])
        self.page.update()
    ####################
    # サムネイルグリッド表示がされているときの画面
    ####################
    def update_thumbnail_view(self, count, path):
        self.metadata_text.controls.clear()
        self.metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text(f"サムネイルビュー: {count} 枚", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(path, size=12, color=ft.Colors.OUTLINE),
        ])
        self.page.update()
    ####################
    # メタデータ表示の更新
    ####################
    def update_metadata(self, image_path: str):
        theme_colors = self.theme_manager.colors
        self.metadata_text.controls.clear()
        if not image_path:
            self.update_no_selection()
            return
        try:
            stat = os.stat(image_path)
            size_kb = stat.st_size / 1024
            self.metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text("PNG メタデータ", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
            ])
            # tEXt / zTXt / iTXt 解析
            with open(image_path, "rb") as f:
                reader = png.Reader(file=f)
                for chunk_type, data in reader.chunks():
                    ctype = chunk_type.decode("latin1", errors="ignore")
                    if ctype == "tEXt":
                        text = data.decode("latin1", errors="ignore")
                        if "::" in text:
                            k, v = text.split("::", 1)
                            self.add_divider_and_text(f"{ctype}: {k}: {v}")
                        else:
                            positive_index = text.find('parameters')
                            negative_index = text.find('Negative prompt: ')
                            anothers_index = text.find('Steps: ')
                            if positive_index != -1:
                                if negative_index == -1:
                                    prompt_text = text[positive_index+11:anothers_index].strip()
                                    other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                    self.add_prompt_section(prompt_text)
                                    self.add_other_section(other_info)
                                else:
                                    prompt_text = text[positive_index+11:negative_index].strip()
                                    negative_text = text[negative_index+17:anothers_index].strip()
                                    other_info = text[anothers_index+7:].strip().replace(", ", "\n")
                                    self.add_prompt_section(prompt_text)
                                    self.add_negative_section(negative_text)
                                    self.add_other_section(other_info)
                            else:
                                self.add_divider_and_text(f"{ctype}: {text}")
                    elif ctype == "zTXt":
                        self.add_divider_and_text(f"{ctype}: ", weight_bold=True)
                        try:
                            keyword_end = data.index(b"\0")
                            keyword = data[:keyword_end].decode("latin1")
                            compressed = data[keyword_end+2:]
                            decompressed = zlib.decompress(compressed)
                            text = decompressed.decode("utf-8", errors="replace")
                            self.metadata_text.controls.append(ft.Text(f"{keyword}: {text}"))
                        except Exception as e:
                            self.metadata_text.controls.append(ft.Text(f"デコード失敗({e})", color=ft.Colors.RED))
                    elif ctype == "iTXt":
                        self.add_divider_and_text(f"{ctype}: ", weight_bold=True)
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
                            if compression_flag == 1:
                                if compression_method != 0:
                                    text = f"不明な圧縮方式"
                                else:
                                    text = zlib.decompress(text_data).decode("utf-8", errors="replace")
                            else:
                                text = text_data.decode("utf-8", errors="replace")
                            if lang_tag != "":
                                self.metadata_text.controls.append(ft.Text(f"language tag: {lang_tag}"))
                            if translated_keyword != "":
                                self.metadata_text.controls.append(ft.Text(f"translated keyword: {translated_keyword}"))
                            self.metadata_text.controls.append(ft.Text(f"{keyword}: {text}"))
                        except Exception as e:
                            self.metadata_text.controls.append(ft.Text(f"デコード失敗({e})", color=ft.Colors.RED))
            # ファイル情報
            self.metadata_text.controls.extend([
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text(f"ファイル情報", weight=ft.FontWeight.BOLD, size=16, color=theme_colors["meta_secondary_title"]),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.Text(f"名前: {Path(image_path).name}"),
                ft.Text(f"サイズ: {size_kb:.1f} KB"),
                ft.Text(f"更新日時: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y/%m/%d %H:%M')}"),
            ])
            # IHDR
            reader = png.Reader(filename=image_path)
            w, h, _, info = reader.read()
            self.metadata_text.controls.extend([
                ft.Text(f"幅 × 高さ: {w} × {h} px"),
                ft.Text(f"ビット深度: {info.get('bitdepth')}"),
                ft.Text(f"透明度: {'あり' if info.get('alpha') else 'なし'}"),
            ])
        except Exception as e:
            self.metadata_text.controls.append(ft.Text(f"エラー: {e}", color="red"))
        self.page.update()
    ####################
    # 水平線とテキストの追加
    ####################
    def add_divider_and_text(self, text, weight_bold=False):
        self.metadata_text.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
        self.metadata_text.controls.append(ft.Text(text, weight=ft.FontWeight.BOLD if weight_bold else ft.FontWeight.NORMAL))
    ####################
    # ポジティブプロンプトの表示部分
    ####################
    def add_prompt_section(self, prompt_text):
        row = ft.Row([
            ft.Text("プロンプト", weight=ft.FontWeight.BOLD, size=14),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="プロンプトをコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, prompt_text, "プロンプト")
            )
        ])
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(ft.Text(prompt_text, size=13))
    ####################
    # ネガティブプロンプトの表示部分
    ####################
    def add_negative_section(self, negative_text):
        row = ft.Row([
            ft.Text("ネガティブプロンプト", weight=ft.FontWeight.BOLD, size=14),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="ネガティブプロンプトをコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, negative_text, "ネガティブプロンプト")
            )
        ])
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(ft.Text(negative_text, size=13))
    ####################
    # その他情報の表示部分
    ####################
    def add_other_section(self, other_info):
        row = ft.Row([
            ft.Text("その他情報", weight=ft.FontWeight.BOLD, size=14),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="その他情報をコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, f"Steps: {other_info}", "その他情報")
            )
        ])
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(ft.Text(f"Steps: {other_info}", size=13))