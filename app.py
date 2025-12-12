import flet as ft
import threading
import time
import win32gui
import win32api
import win32con
import warnings

from panels.left_panel import LeftPanel
from panels.center_panel import CenterPanel
from panels.right_panel import RightPanel
from panels.appbar import CustomAppBar
from utils.settings import SettingsManager
from utils.themes import ThemeManager

warnings.filterwarnings('ignore', category=DeprecationWarning)

class ImageViewerApp:
    # 初期化
    def __init__(self):
        self.settings = SettingsManager.load()
        self.theme_manager = ThemeManager(self.settings)
    # イベント：ウインドウを閉じる
    def on_window_close(self, e):
        if e.data == "close":
            SettingsManager.save(self.settings)
            e.page.window.prevent_close = False
            e.page.window.close()
    # イベント：ウインドウハンドル
    def setup_window_handle(self, page: ft.Page):
        def find_handle():
            time.sleep(0.6)
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and page.title in win32gui.GetWindowText(hwnd):
                    page.window_handle = hwnd
                    return False
            win32gui.EnumWindows(callback, None)
        threading.Thread(target=find_handle, daemon=True).start()
    # イベント：マウスナビゲーション
    def setup_mouse_navigation(self, page: ft.Page):
        def listener():
            while True:
                if not hasattr(page, "window_handle") or not page.window_handle:
                    time.sleep(0.1)
                    continue
                if win32gui.GetForegroundWindow() == page.window_handle:
                    if win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:
                        page.run_task(self.left_panel.go_back)
                        while win32api.GetKeyState(win32con.VK_XBUTTON1) < 0:
                            time.sleep(0.01)
                        time.sleep(0.08)
                    if win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:
                        page.run_task(self.left_panel.go_forward)
                        while win32api.GetKeyState(win32con.VK_XBUTTON2) < 0:
                            time.sleep(0.01)
                        time.sleep(0.08)
                time.sleep(0.01)
        threading.Thread(target=listener, daemon=True).start()
    # イベント：ウインドウの最大化、復元
    def toggle_maximize(self, page: ft.Page, maxmize_button):
        page.window.maximized = not page.window.maximized
        if page.window.maximized:
            maxmize_button.icon = ft.Icons.FULLSCREEN_EXIT
            maxmize_button.tooltip = "元に戻す"
        else:
            maxmize_button.icon = ft.Icons.FULLSCREEN
            maxmize_button.tooltip = "最大化"
        page.update()
    def minimize(self, page: ft.Page):
        page.window.minimized = not page.window.maximized
        page.update()
    ####################
    # メイン関数
    ####################
    def main(self, page: ft.Page):
        page.title = "PNG Image Viewer with Metadata"
        page.window.title_bar_hidden = True 
        page.window.min_width = 1024
        page.window.min_height = 576
        page.window.width = 1440
        page.window.height = 810
        page.window.resizable = True
        page.window.prevent_close = True
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 0
        # カスタム属性
        page.navigation_history = ["<DRIVES>"]
        page.history_index = 0
        page.current_image_path = None
        page.scroll_position_history_left = []
        page.scroll_position_history_center = []
        # パネル初期化
        self.appbar       = CustomAppBar(page, self.settings, self.theme_manager)
        self.center_panel = CenterPanel(page, self.settings, self.theme_manager)
        self.right_panel  = RightPanel(page, self.settings, self.theme_manager)
        self.left_panel   = LeftPanel(page, self.settings, self.theme_manager)
        # ローディングオーバーレイ
        loading_overlay = ft.Container(
            visible=False,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.88, ft.Colors.BLACK),
            alignment=ft.alignment.center,
            content=ft.Column([
                ft.ProgressRing(width=60, height=60, stroke_width=7, color=ft.Colors.CYAN_400),
                ft.Text("読み込み中…", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24),
        )
        page.overlay.append(loading_overlay)
        # カスタムアプリケーションバー
        app_icon = ft.Container(
            content=ft.Icon(ft.Icons.IMAGE_OUTLINED, color=ft.Colors.WHITE),
            width=40, height=40,
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(0),
            ink=True, bgcolor=ft.Colors.BLUE,
        )
        minimize_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.MINIMIZE,
                bgcolor=ft.Colors.BLUE,
                icon_color=ft.Colors.WHITE,
                tooltip="最小化",
                padding=ft.padding.all(0),
                on_click=lambda _: self.minimize(page),
            ),
            width=40, height=40,
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(0),
            ink=True, bgcolor=ft.Colors.BLUE,
        )
        maxmize_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.FULLSCREEN,
                bgcolor=ft.Colors.BLUE,
                icon_color=ft.Colors.WHITE,
                tooltip="最大化",
                padding=ft.padding.all(0),
                on_click=lambda _: self.toggle_maximize(page, maxmize_button.content),
            ),
            width=40, height=40,
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(0),
            ink=True, bgcolor=ft.Colors.BLUE,
        )
        close_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.CLOSE,
                bgcolor=ft.Colors.BLUE,
                icon_color=ft.Colors.WHITE,
                tooltip="閉じる",
                padding=ft.padding.all(0),
                on_click=lambda _: self.toggle_maximize(page, page.window.close()),
            ),
            width=40, height=40,
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(0),
            ink=True, bgcolor=ft.Colors.BLUE,
        )
        custom_appbar = ft.Row([
            ft.WindowDragArea(
                ft.Row([
                    app_icon,
                    ft.Container(
                        ft.Text("PNG Image Viewer with Metadata", size=18,color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.BLUE,
                        padding=7,
                        expand=True,
                    ),
                ], expand=True, spacing=0),
                expand=True,
            ),
            minimize_button,
            maxmize_button,
            close_button,
        ],spacing=0)
        # テーマ適用
        self.theme_manager.apply_to_app(page, self.left_panel, self.center_panel, self.right_panel)
        # 最終配置
        page.add(
            ft.Column([
                self.appbar.container,
                ft.Row([
                    self.left_panel.container,
                    self.center_panel.container,
                    self.right_panel.container,
                ], expand=True, spacing=0)
            ], expand=True, spacing=0)
        )
        # 初期表示
        self.left_panel.navigate_to("<DRIVES>")
        # イベント設定
        page.window.on_event = self.on_window_close
        self.setup_mouse_navigation(page)
        self.setup_window_handle(page)