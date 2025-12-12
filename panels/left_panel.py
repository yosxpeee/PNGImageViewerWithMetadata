import flet as ft
import os
import string
from pathlib import Path
import win32api

from panels.center_panel import CenterPanel
from panels.right_panel import RightPanel
from utils.scroll_record import record_left_scroll_position, replay_left_scroll_position

class LeftPanel:
    instance = None
    # 初期化
    def __init__(self, page, settings, theme_manager):
        self.page = page
        self.settings = settings
        self.theme_manager = theme_manager
        LeftPanel.instance = self
        page.current_path_text = ft.Text("", size=12, color=theme_manager.colors["text_secondary"])
        self.current_path_text = page.current_path_text
        self.dir_list = ft.ListView(
            expand=True,
            spacing=0,
            padding=0,
            on_scroll=self.on_browser_scroll,
        )
        self.theme_switch = ft.Switch(
            value=settings["dark_theme"],
            on_change=self.toggle_theme,
            label="ダークモード",
            label_position=ft.LabelPosition.LEFT,
            height=36,
        )
        self.container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EXPLORE),
                    ft.Text("ファイルブラウザ", weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    self.theme_switch,
                ]),
                self.current_path_text,
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                self.dir_list,
            ], expand=True),
            padding=10,
            width=340,
            bgcolor=theme_manager.colors["bg_panel"],
        )
    # イベント：トグルスイッチによるテーマ切り替え
    def toggle_theme(self, e):
        # スイッチの値で設定を更新
        self.settings["dark_theme"] = self.theme_switch.value
        # 色を更新
        self.theme_manager.update_colors()
        # テーマを全パネルに適用
        self.theme_manager.apply_to_app(
            self.page,
            self,
            CenterPanel.instance,
            RightPanel.instance
        )
    # イベント：ファイルブラウザのスクロール
    def on_browser_scroll(self, e):
        if e.data:
            import json
            scroll_pos = json.loads(e.data)
            record_left_scroll_position(self.page, self.current_path_text, scroll_pos)
    ####################
    # ナビゲート処理
    ####################
    def navigate_to(self, path: str):
        if self.page.history_index + 1 < len(self.page.navigation_history):
            self.page.navigation_history = self.page.navigation_history[:self.page.history_index + 1]
        self.page.navigation_history.append(path)
        self.page.history_index += 1
        self.refresh_directory(path)
    ####################
    # ディレクトリの表示更新
    ####################
    def refresh_directory(self, path: str):
        self.dir_list.controls.clear()
        self.page.current_image_path = None
        theme_colors = self.theme_manager.colors
        # ── ドライブ一覧の特別処理 ──
        if path == "<DRIVES>":
            self.current_path_text.value = "ドライブを選択してください"

            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        label = win32api.GetVolumeInformation(drive)[0] or "ローカルディスク"
                        self.dir_list.controls.append(self.make_list_item(
                            f"{drive} [{label}]",
                            ft.Icons.STORAGE,
                            path=drive,
                            is_folder=True,
                            theme_colors=theme_colors
                        ))
                    except:
                        # アクセスできないドライブ（CD-ROM空など）は無視
                        pass
            # ドライブ一覧ではサムネイル非表示
            if CenterPanel.instance:
                CenterPanel.instance.show_no_images()
        # ── 通常のフォルダ処理 ──
        else:
            p = Path(path)
            self.current_path_text.value = f"現在: {path}"
            # サムネイル読み込み判定
            try:
                has_png = any(item.suffix.lower() == ".png" for item in p.iterdir())
                if has_png:
                    self.page.run_task(CenterPanel.instance.show_thumbnails_async, path)
                else:
                    CenterPanel.instance.show_no_images()
            except PermissionError:
                CenterPanel.instance.show_no_images()
            # 「ドライブ一覧に戻る」ボタン
            back = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.COMPUTER, size=14),
                    ft.Text("ドライブ一覧に戻る", size=14),
                ]),
                height=32,
                alignment=ft.alignment.top_center,
                padding=ft.padding.symmetric(horizontal=1, vertical=1),
                border_radius=8,
                ink=True,
                on_click=lambda _: self.navigate_to("<DRIVES>"),
                on_hover=lambda e: (
                    setattr(e.control, "bgcolor", theme_colors["selected"] if e.data == "true" else None),
                    e.control.update()
                )
            )
            self.dir_list.controls.append(back)
            self.dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
            # 親フォルダ
            if p.parent != p:
                self.dir_list.controls.append(self.make_list_item(
                    ".. (親フォルダ)",
                    ft.Icons.ARROW_BACK,
                    path=str(p.parent),
                    is_folder=True,
                    theme_colors=theme_colors
                ))
            # ファイル・フォルダ一覧
            try:
                items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    if item.is_dir():
                        self.dir_list.controls.append(self.make_list_item(
                            item.name + "/",
                            ft.Icons.FOLDER,
                            path=str(item),
                            is_folder=True,
                            theme_colors=theme_colors
                        ))
                    elif item.suffix.lower() == ".png":
                        self.dir_list.controls.append(self.make_list_item(
                            item.name,
                            ft.Icons.IMAGE,
                            path=str(item),
                            theme_colors=theme_colors
                        ))
            except PermissionError:
                self.dir_list.controls.append(ft.Text("アクセス拒否", color="red"))
        # スクロール位置復元（共通）
        replay_left_scroll_position(self.page, self.current_path_text, self.dir_list)
        self.page.update()
    ####################
    # リスト表示部分の生成
    ####################
    def make_list_item(self, name: str, icon, path: str, is_folder=False, theme_colors=None):
        if theme_colors is None:
            theme_colors = self.theme_manager.colors
        # イベント：クリック
        def on_click_handler(e):
            if is_folder:
                self.navigate_to(path)
            else:
                CenterPanel.instance.select_image(path)
        # イベント：ホバーエフェクト
        def mli_hover(e):
            container.bgcolor = theme_colors["hover"] if e.data == "true" else None
            container.update()

        container = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=14),
                ft.Text(name, expand=True, size=14),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, opacity=0.5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            height=24,
            padding=ft.padding.symmetric(horizontal=1, vertical=1),
            border_radius=8,
            ink=True,
            on_click=on_click_handler,
        )
        container.on_hover = mli_hover
        return container
    ####################
    # マウスの戻るボタン処理
    ####################
    async def go_back(self):
        if self.page.history_index > 0:
            self.page.history_index -= 1
            self.refresh_directory(self.page.navigation_history[self.page.history_index])
        self.page.update()
    ####################
    # マウスの進むボタン処理
    ####################
    async def go_forward(self):
        if self.page.history_index + 1 < len(self.page.navigation_history):
            self.page.history_index += 1
            self.refresh_directory(self.page.navigation_history[self.page.history_index])
        self.page.update()
    