import flet as ft
from pathlib import Path
from PIL import Image
import base64
import io
import os
import asyncio

from panels.right_panel import RightPanel
from utils.scroll_record import record_center_scroll_position, replay_center_scroll_position
from utils.clipboard import copy_image_to_clipboard

class CenterPanel:
    instance = None
    # 初期化
    def __init__(self, page, settings, theme_manager, mode):
        self.page = page
        self.settings = settings
        self.theme_manager = theme_manager
        self.mode = mode
        CenterPanel.instance = self
        self.interrupt_current_process = False
        self.image_view = ft.Image(
            src="",
            fit=ft.ImageFit.CONTAIN,
            expand=True,
            visible=False,
        )
        self.thumbnail_grid = ft.GridView(
            runs_count=5,
            max_extent=180,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            padding=20,
            visible=False,
            on_scroll=self.on_grid_scroll,
        )
        center_content_stack = ft.Stack([
            self.image_view,
            self.thumbnail_grid,
        ], expand=True)
        self.container = ft.Container(
            content=ft.GestureDetector(
                content=center_content_stack,
                on_secondary_tap_down=self.show_image_context_menu,
                on_tap_down=self.return_to_grid,
            ),
            alignment=ft.alignment.center,
            expand=2,
            bgcolor=theme_manager.colors["bg_main"],
        )
    # イベント：サムネイルグリッドのスクロール
    def on_grid_scroll(self, e):
        if e.data:
            import json
            scroll_pos = json.loads(e.data)
            record_center_scroll_position(self.page, self.page.current_path_text, scroll_pos)
    # イベント：サムネイルグリッド表示に戻る
    def return_to_grid(self, e):
        if self.image_view.visible:
            self.thumbnail_grid.visible = True
            self.image_view.visible = False
            self.page.current_image_path = None
            for container in self.thumbnail_grid.controls:
                if hasattr(container, "animate_scale") and container.scale != 1.0:
                    container.scale = 1.0
                    container.update()
            if self.mode == "browser":
                title = "フォルダ内画像"
            else:
                title = "検索結果"
            RightPanel.instance.update_thumbnail_view(len(self.thumbnail_grid.controls), title)
            replay_center_scroll_position(self.page, self.page.current_path_text, self.thumbnail_grid)
            self.page.update()
    # イベント：右クリックメニュー表示
    def show_image_context_menu(self, e: ft.TapDownEvent):
        if self.thumbnail_grid.visible or not self.image_view.visible:
            return
        current_path = self.page.current_image_path
        if not current_path or not os.path.exists(current_path):
            return
        menu_x = e.global_x
        menu_y = e.global_y
        self.create_image_context_menu(menu_x, menu_y, current_path)
    ####################
    # モード切替
    ####################
    def switch_mode(self, mode):
        self.mode = mode
    ####################
    # サムネイルグリッド表示（閲覧モード）
    ####################
    async def show_thumbnails_async(self, folder_path: str):
        loading_overlay = self.page.overlay[1]
        loading_overlay.visible = True
        loading_overlay.name = "loading"
        loading_overlay.content.controls[2].value = "読み込み中…"
        self.page.update()
        await asyncio.sleep(0.1)
        self.thumbnail_grid.controls.clear()
        try:
            png_files = [p for p in Path(folder_path).iterdir() if p.suffix.lower() == ".png"]
            png_files = sorted(png_files, key=lambda x: x.name.lower())
        except Exception as e:
            loading_overlay.visible = False
            RightPanel.instance.update_no_selection()
            self.page.update()
            return
        if not png_files:
            loading_overlay.visible = False
            self.show_no_images()
            return
        self.image_view.visible = False
        self.thumbnail_grid.visible = True
        for i, png_path in enumerate(png_files):
            # 履歴操作されたら即座に中止
            if self.page.navigation_history[self.page.history_index] != folder_path:
                loading_overlay.visible = False
                self.page.update()
                return
            try:
                with Image.open(png_path) as img:
                    img.thumbnail((160, 160))
                    byte_io = io.BytesIO()
                    img.save(byte_io, format="PNG")
                    base64_str = base64.b64encode(byte_io.getvalue()).decode()
                container = ft.Container(
                    width=160, height=160,
                    border_radius=12,
                    padding=6,
                    bgcolor=ft.Colors.GREY,
                    alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, "#000000")),
                    animate_scale=ft.Animation(300, "ease_out_back"),
                    scale=1.0,
                    content=ft.Image(src_base64=base64_str, fit=ft.ImageFit.CONTAIN),
                )
                container.on_hover = lambda e, c=container: (setattr(c, "scale", 1.12 if e.data == "true" else 1.0) or c.update())
                container.on_click = lambda e, p=str(png_path): self.select_image(p)
                self.thumbnail_grid.controls.append(container)

                if i % 50 == 0 or i == len(png_files) - 1:
                    percent = int((i + 1) / len(png_files) * 100)
                    loading_overlay.content.controls[2].value = f"読み込み中… {i+1}/{len(png_files)} ({percent}%)"
                    self.page.update()
                    await asyncio.sleep(0.01)
            except Exception as e:
                self.page.open(ft.SnackBar(
                    content=ft.Text(f"サムネイル生成失敗 {png_path}: {e}", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_700,
                    duration=1500,
                ))
        loading_overlay.visible = False
        RightPanel.instance.update_thumbnail_view(len(self.thumbnail_grid.controls), "フォルダ内画像")
        replay_center_scroll_position(self.page, self.page.current_path_text, self.thumbnail_grid)
        self.page.update()
    ####################
    # サムネイルグリッド表示（検索モード）
    ####################
    async def show_thumbnails_from_list_async(self, file_paths: list[str]):
        loading_overlay = self.page.overlay[1]
        loading_overlay.visible = True
        loading_overlay.name = "loading"
        loading_overlay.content.controls[2].value = "読み込み中…"
        self.page.update()
        await asyncio.sleep(0.1)
        self.thumbnail_grid.controls.clear()
        self.image_view.visible = False
        self.thumbnail_grid.visible = True
        for i, png_path in enumerate(file_paths):
            try:
                with Image.open(png_path) as img:
                    if self.interrupt_current_process == True:
                        #中断した旨表示
                        self.page.open(ft.SnackBar(
                            content=ft.Text("サムネイル表示を中断しました。", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.RED_700,
                            duration=1500,
                        ))
                        #右ペインの表示変更
                        RightPanel.instance.update_no_images_search()
                        #中央ペインのクリア
                        self.thumbnail_grid.controls.clear()
                        self.thumbnail_grid.visible = True
                        #オーバーレイ解除
                        loading_overlay.visible = False
                        self.page.update()
                        #キャンセルフラグリセット
                        self.interrupt_current_process = False
                        from panels.left_panel import LeftPanel #強引
                        LeftPanel.instance.interrupt_current_process = False
                        return
                    img.thumbnail((160, 160))
                    byte_io = io.BytesIO()
                    img.save(byte_io, format="PNG")
                    base64_str = base64.b64encode(byte_io.getvalue()).decode()
                container = ft.Container(
                    width=160, height=160,
                    border_radius=12,
                    padding=6,
                    bgcolor=ft.Colors.GREY,
                    alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.3, "#000000")),
                    animate_scale=ft.Animation(300, "ease_out_back"),
                    scale=1.0,
                    content=ft.Image(src_base64=base64_str, fit=ft.ImageFit.CONTAIN),
                )
                container.on_hover = lambda e, c=container: (setattr(c, "scale", 1.12 if e.data == "true" else 1.0) or c.update())
                container.on_click = lambda e, p=png_path: self.select_image(p)
                self.thumbnail_grid.controls.append(container)
                if i % 50 == 0 or i == len(file_paths) - 1:
                    percent = int((i + 1) / len(file_paths) * 100)
                    loading_overlay.content.controls[2].value = f"読み込み中… {i+1}/{len(file_paths)} ({percent}%)"
                    self.page.update()
                    await asyncio.sleep(0.01)
            except Exception as e:
                self.page.open(ft.SnackBar(
                    content=ft.Text(f"サムネイル生成失敗 {png_path}: {e}", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_700,
                    duration=1500,
                ))
        loading_overlay.visible = False
        #表示しきったら念のためキャンセルフラグリセット
        self.interrupt_current_process = False
        CenterPanel.instance.interrupt_current_process = False
        RightPanel.instance.update_thumbnail_view(len(file_paths), "検索結果")
        self.page.update()
    ####################
    # 画像を選択する
    ####################
    def select_image(self, path: str):
        self.page.current_image_path = path
        self.image_view.src = path
        self.image_view.visible = True
        self.thumbnail_grid.visible = False
        RightPanel.instance.update_metadata(path)
        self.page.update()
    ####################
    # 右クリックメニューの作成
    ####################
    def create_image_context_menu(self, menu_x, menu_y, current_path):
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
                    title=ft.Text("画像をクリップボードにコピー\n(透明度維持)", size=12),
                    on_click=lambda e: (
                        copy_image_to_clipboard(self.page, current_path, True),
                        self.page.overlay.pop(),
                        self.page.open(ft.SnackBar(
                            content=ft.Text("画像をクリップボードにコピーしました！(透明度あり)" ,color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.GREEN_700,
                            duration=1500,
                        )),
                        self.page.update()
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.COPY, size=18),
                    title=ft.Text("画像をクリップボードにコピー\n(透明度なし)", size=12),
                    on_click=lambda e: (
                        copy_image_to_clipboard(self.page, current_path, False),
                        self.page.overlay.pop(),
                        self.page.open(ft.SnackBar(
                            content=ft.Text("画像をクリップボードにコピーしました！(透明度なし)", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.GREEN_700,
                            duration=1500,
                        )),
                        self.page.update()
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FOLDER_OPEN, size=18),
                    title=ft.Text("フォルダをエクスプローラーで開く", size=12),
                    on_click=lambda e: (
                        __import__("subprocess").Popen(f'explorer /select,"{current_path}"'),
                        self.page.overlay.pop(),
                        self.page.update()
                    ),
                ),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CLOSE, size=18),
                    title=ft.Text("キャンセル", size=12, color=ft.Colors.ERROR),
                    on_click=lambda e: (
                        self.page.overlay.pop(),
                        self.page.update()
                    ),
                ),
            ], spacing=0),
        )
        overlay = ft.Stack([
            ft.Container(bgcolor=ft.Colors.TRANSPARENT, on_click=lambda e: (self.page.overlay.pop(), self.page.update()), expand=True),
            ft.Container(content=context_menu, top=menu_y - 100, left=menu_x - 120, animate=ft.Animation(150, "decelerate")),
        ], expand=True)
        self.page.overlay.append(overlay)
        self.page.update()
    ####################
    # 画像を非表示にする
    ####################
    def show_no_images(self):
        self.image_view.visible = False
        self.thumbnail_grid.visible = False
        RightPanel.instance.update_no_images()
        self.page.update()