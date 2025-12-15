import flet as ft
import os
import png
from pathlib import Path
from datetime import datetime

from utils.right_click_menu import copy_text_to_clipboard
from utils.get_metadata import get_zTxt, get_iTXt, get_tEXt

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
    ####################
    def update_no_images(self):
        self.metadata_text.controls.clear()
        self.metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("このフォルダにPNG画像がありません", size=16),
        ])
        self.page.update()
    def update_no_images_search(self):
        self.metadata_text.controls.clear()
        self.metadata_text.controls.extend([
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Text("検索条件に一致する画像がありません。", size=16),
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
                        text, prompt_text, negative_text, other_info = get_tEXt(data)
                        if text != "":
                            self.add_divider_and_text(f"{ctype}: ", weight_bold=True)
                            self.metadata_text.controls.append(ft.Text(text))
                        else:
                            if prompt_text != "":
                                self.add_prompt_section(prompt_text)
                            if negative_text != "":
                                self.add_negative_section(negative_text)
                            if other_info != "":
                                self.add_other_section(other_info)
                    elif ctype == "zTXt":
                        self.add_divider_and_text(f"{ctype}: ", weight_bold=True)
                        text = get_zTxt(data)
                        self.metadata_text.controls.append(ft.Text(text))
                    elif ctype == "iTXt":
                        self.add_divider_and_text(f"{ctype}: ", weight_bold=True)
                        text = get_iTXt(data)
                        self.metadata_text.controls.append(ft.Text(text))
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
    # コピーできるテキスト
    ####################
    def make_copyable_text(self, value: str, size=12):
        return ft.TextField(
            value=value,
            read_only=True,
            multiline=True,
            border="none",
            text_size=size,
            min_lines=1,
            max_lines=100,
        )
    ####################
    # ポジティブプロンプトの表示部分
    ####################
    def add_prompt_section(self, prompt_text):
        row = ft.Row([
            ft.Text(
                spans=[
                    ft.TextSpan("プロンプト", ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE))
                ],
                weight=ft.FontWeight.BOLD, size=14
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="プロンプトをコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, prompt_text, "プロンプト")
            )
        ], height=24)
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(self.make_copyable_text(prompt_text, 13))
    ####################
    # ネガティブプロンプトの表示部分
    ####################
    def add_negative_section(self, negative_text):
        row = ft.Row([
            ft.Text(
                spans=[
                    ft.TextSpan("ネガティブプロンプト", ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE))
                ],
                weight=ft.FontWeight.BOLD, size=14
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="ネガティブプロンプトをコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, negative_text, "ネガティブプロンプト")
            )
        ], height=24)
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(self.make_copyable_text(negative_text, 13))
    ####################
    # その他情報の表示部分
    ####################
    def add_other_section(self, other_info):
        row = ft.Row([
            ft.Text(
                spans=[
                    ft.TextSpan("その他情報", ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE))
                ],
                weight=ft.FontWeight.BOLD, size=14
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.COPY,
                icon_size=14,
                tooltip="その他情報をコピー",
                on_click=lambda e: copy_text_to_clipboard(self.page, f"Steps: {other_info}", "その他情報")
            )
        ], height=24)
        self.metadata_text.controls.append(ft.Container(content=row, padding=ft.padding.only(top=0, bottom=0)))
        self.metadata_text.controls.append(self.make_copyable_text(f"Steps: {other_info}", 13))