import flet as ft
import os
import string
from pathlib import Path
import win32api
import png
import asyncio

from panels.center_panel import CenterPanel
from panels.right_panel import RightPanel
from utils.scroll_record import record_left_scroll_position, replay_left_scroll_position
from utils.get_metadata import get_tEXt

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
        self.search_folder_text = ft.Text("検索フォルダ: 未選択", size=12, width=270)
        self.search_folder_path = None  # 実際に選んだパス
        # 一番左のモード切り替えパネ(ルナビゲーションレール)
        self.navi_rail = ft.NavigationRail(
            selected_index=0,
            min_width=60,
            width=60,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.REMOVE_RED_EYE_OUTLINED,
                    selected_icon=ft.Icons.REMOVE_RED_EYE,
                    label="閲覧",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SEARCH_OUTLINED,
                    selected_icon=ft.Icons.SEARCH,
                    label="検索",
                ),
            ],
            on_change=self.switch_right_item,
        )

        # 閲覧/検索のどちらにも置くアイテム
        self.theme_switch = ft.Switch(
            value=settings["dark_theme"],
            on_change=self.toggle_theme,
            label="ダークモード",
            label_position=ft.LabelPosition.LEFT,
            height=36,
        )
        # 検索用アイテム
        self.pick_folder_button = ft.ElevatedButton(
            "検索フォルダを選択",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.pick_folder,
        )
        self.search_target_filename = ft.TextField(
            label="ファイル名に含む文字列",
            hint_text="例: 20251012",
            width=270,
            height=36,
            border_color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE),
        )
        self.search_target_itxt = ft.TextField(
            label="メタデータ(tEXt)に含む文字列",
            hint_text="例: long hair",
            width=270,
            height=36,
            border_color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE),
        )
        self.search_button = ft.ElevatedButton(
            "検索実行",
            icon=ft.Icons.SEARCH,
            on_click=lambda e: self.page.run_task(self.perform_search),
            disabled=True,  # フォルダ未選択時は無効
        )
        self.search = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SEARCH),
                ft.Text("ファイル検索", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.theme_switch,
            ]),
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            ft.Row([
                self.pick_folder_button,
                ft.ElevatedButton(
                    "クリア", 
                    icon=ft.Icons.CLEAR,
                    on_click=self.clear_search_fields
                ),
            ]),
            self.search_folder_text,
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)),
            self.search_target_filename,
            self.search_target_itxt,
            self.search_button,
        ], expand=True)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_picked)
        self.folder_picker.name = "picker"
        page.overlay.append(self.folder_picker)
        # 閲覧用アイテム
        self.dir_list = ft.ListView(
            expand=True,
            spacing=0,
            padding=0,
            on_scroll=self.on_browser_scroll,
        )
        self.browser = ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.SPACE_DASHBOARD),
                ft.Text("ファイルブラウザ", weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.theme_switch,
            ]),
            self.current_path_text,
            self.dir_list,
        ], expand=True)
        self.container = ft.Container(
            content= ft.Row([
                self.navi_rail,
                self.browser, #初期状態は閲覧モード固定
            ]),
            padding=10,
            width=360,
            bgcolor=theme_manager.colors["bg_panel"],
        )
    # イベント：右アイテムの切り替え
    def switch_right_item(self, e):
        if e.control.selected_index == 0:
            right_item = self.browser
            CenterPanel.instance.switch_mode("browser")
        else:
            right_item = self.search
            CenterPanel.instance.switch_mode("search")
        self.container.content.controls[1] = right_item
        #中央ペインはクリアして直前の処理をやり直す
        CenterPanel.instance.image_view.visible = False
        CenterPanel.instance.thumbnail_grid.visible = False
        CenterPanel.instance.thumbnail_grid.controls.clear()
        if e.control.selected_index == 0:
            if self.current_path_text.value == "ドライブを選択してください":
                self.refresh_directory("<DRIVES>")
            else:
                self.refresh_directory(self.current_path_text.value)
        else:
            self.page.run_task(self.perform_search)
        self.page.update()
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
    # イベント：ファイルピッカー
    def pick_folder(self, e):
        self.folder_picker.get_directory_path(dialog_title="検索対象のフォルダを選択")
    def on_folder_picked(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.search_folder_path = e.path
            self.search_folder_text.value = f"検索フォルダ: {e.path}"
            self.search_button.disabled = False
        else:
            self.search_folder_path = None
            self.search_folder_text.value = "検索フォルダ: 未選択"
            self.search_button.disabled = True
        self.page.update()
    # イベント：検索ディレクトリ指定の解除
    def clear_search_fields(self, e):
        self.search_folder_path = None
        self.search_folder_text.value = "検索フォルダ: 未選択"
        self.search_button.disabled = True
        RightPanel.instance.update_no_images_search()
        self.page.update()
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
            self.current_path_text.value = f"{path}"
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
            self.dir_list.controls.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE)))
            back = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.COMPUTER, size=14),
                    ft.Text("ドライブ一覧に戻る", size=14),
                ]),
                height=32,
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
        self.settings["last_dir"] = path
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
        # 閲覧モード時のみ反応
        if self.navi_rail.selected_index == 0:
            if self.page.history_index > 0:
                self.page.history_index -= 1
                self.refresh_directory(self.page.navigation_history[self.page.history_index])
            self.page.update()
    ####################
    # マウスの進むボタン処理
    ####################
    async def go_forward(self):
        # 閲覧モード時のみ反応
        if self.navi_rail.selected_index == 0:
            if self.page.history_index + 1 < len(self.page.navigation_history):
                self.page.history_index += 1
                self.refresh_directory(self.page.navigation_history[self.page.history_index])
            self.page.update()
    ####################
    # 検索実行（非同期）
    ####################
    async def perform_search(self):
        if not self.search_folder_path:
            RightPanel.instance.update_no_images_search()
            return
        folder = Path(self.search_folder_path)
        if not folder.exists():
            self.page.open(ft.SnackBar(
                content=ft.Text("フォルダが存在しません", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                duration=1500,
            ))
            self.page.update()
            return
        name_query = self.search_target_filename.value.strip().lower()
        tExt_query = self.search_target_itxt.value.strip().lower()
        loading = self.page.overlay[1]
        loading.visible = True
        loading.content.controls[2].value = "検索中…"
        self.page.update()
        await asyncio.sleep(0.1)
        # 再帰的にPNGを検索
        results = []
        png_files = folder.rglob("*.png")
        all_file_num = len(list(png_files))
        png_files = folder.rglob("*.png") # listにすると消費しきられるのでもう一回とる
        i = 0
        for png_path in png_files:
            found_text = False
            i += 1
            # ファイル名チェック
            if name_query != "" and name_query not in png_path.name.lower():
                continue
            # メタデータ(tEXt)チェック
            if tExt_query != "":
                try:
                    with open(png_path, "rb") as f:
                        reader = png.Reader(file=f)
                        for chunk_type, data in reader.chunks():
                            ctype = chunk_type.decode("latin1", errors="ignore")
                            if ctype == "tEXt":
                                text, prompt_text, negative_text, other_info = get_tEXt(data)
                                if tExt_query in text:
                                    found_text = True
                                    break
                                if tExt_query in prompt_text:
                                    found_text = True
                                    break
                                if tExt_query in negative_text:
                                    found_text = True
                                    break
                                if tExt_query in other_info:
                                    found_text = True
                                    break
                except Exception as e:
                    # よからぬこと（ファイルが検索中に消えたなど）があっても
                    # そのファイルはスキップして継続
                    continue
            else:
                found_text = True
            if found_text == True:
                results.append(str(png_path))
            # 進捗表示（20個ごとに）
            if i % 20 == 0:
                loading.content.controls[2].value = f"検索中… {i}ファイル処理中/{all_file_num}"
                self.page.update()
                await asyncio.sleep(0.01)
        self.page.update()
        await asyncio.sleep(0.1)
        # 結果表示
        if results:
            await CenterPanel.instance.show_thumbnails_from_list_async(results)
            self.page.open(ft.SnackBar(
                content=ft.Text(f"{len(results)}件の画像が見つかりました！", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
                duration=1500,
            ))
            loading.visible = False
        else:
            CenterPanel.instance.show_no_images()
            self.page.open(ft.SnackBar(
                content=ft.Text("該当する画像が見つかりませんでした", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
                duration=1500,
            ))
            RightPanel.instance.update_no_images_search()
            loading.visible = False #続きの処理がないのでここでオーバーレイを消す
        self.page.update()