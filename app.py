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
    # ウインドウハンドルのセットアップ
    def setup_window_handle(self, page: ft.Page):
        def find_handle():
            time.sleep(0.6)
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and page.title in win32gui.GetWindowText(hwnd):
                    page.window_handle = hwnd
                    return False
            win32gui.EnumWindows(callback, None)
        threading.Thread(target=find_handle, daemon=True).start()
    # マウスナビゲーションのセットアップ
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
    ####################
    # メイン関数
    ####################
    def main(self, page: ft.Page):
        page.title = "PNG Image Viewer with Metadata"
        #page.window.title_bar_hidden = True 
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
        # アプリケーションバーやパネルの初期化
        #self.appbar       = CustomAppBar(page)
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
                ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), #位置調整用
                ft.ProgressRing(width=60, height=60, stroke_width=7, color=ft.Colors.CYAN_400),
                ft.Text("読み込み中…", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=24),
        )
        page.overlay.append(loading_overlay)
        # テーマ適用
        self.theme_manager.apply_to_app(page, self.left_panel, self.center_panel, self.right_panel)
        # 最終配置
        page.add(
            ft.Column([
                #self.appbar.container,
                ft.Row([
                    self.left_panel.container,
                    self.center_panel.container,
                    self.right_panel.container,
                ], expand=True, spacing=0)
            ], expand=True, spacing=0)
        )
        # 初期表示
        self.left_panel.navigate_to(self.settings["last_dir"])
        # イベント設定
        page.window.on_event = self.on_window_close
        self.setup_mouse_navigation(page)
        self.setup_window_handle(page)