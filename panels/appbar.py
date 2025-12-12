import flet as ft

class CustomAppBar:
    def __init__(self, page: ft.Page, settings: dict, theme_manager):
        self.page = page
        self.settings = settings
        self.theme_manager = theme_manager
        # ボタン本体を保持（最大化アイコンの切り替えに必要）
        self.minimize_button = None
        self.maximize_button = None
        self.close_button = None
        self.container = self._build()
    def _build(self) -> ft.Row:
        # アプリアイコン
        app_icon = ft.Container(
            content=ft.Icon(ft.Icons.IMAGE_OUTLINED, color=ft.Colors.WHITE),
            width=40, height=40,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.BLUE,
        )
        # 最小化ボタン
        self.minimize_button = ft.IconButton(
            icon=ft.Icons.MINIMIZE,
            icon_color=ft.Colors.WHITE,
            tooltip="最小化",
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=self._minimize,
        )
        minimize_container = ft.Container(
            content=self.minimize_button,
            width=46, height=40,
            alignment=ft.alignment.center,
            ink=True,
            bgcolor=ft.Colors.BLUE,
        )
        # 最大化／元に戻すボタン
        self.maximize_button = ft.IconButton(
            icon=ft.Icons.FULLSCREEN,
            icon_color=ft.Colors.WHITE,
            tooltip="最大化",
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=self._toggle_maximize,
        )
        maximize_container = ft.Container(
            content=self.maximize_button,
            width=46, height=40,
            alignment=ft.alignment.center,
            ink=True,
            bgcolor=ft.Colors.BLUE,
        )
        # 閉じるボタン
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.WHITE,
            tooltip="閉じる",
            bgcolor=ft.Colors.TRANSPARENT,
            on_click=self._close,
        )
        close_container = ft.Container(
            content=self.close_button,
            width=46, height=40,
            alignment=ft.alignment.center,
            ink=True,
            bgcolor=ft.Colors.BLUE,
        )
        # タイトルバー全体
        return ft.Row(
            controls=[
                ft.WindowDragArea(
                    ft.Container(
                        content=ft.Row(
                            [
                                app_icon,
                                ft.Container(
                                    content=ft.Text(
                                        "PNG Image Viewer with Metadata",
                                        size=18,
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    padding=7,
                                    expand=True,
                                ),
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        bgcolor=ft.Colors.BLUE,
                        height=40,
                        expand=True,
                    ),
                    expand=True,
                ),
                minimize_container,
                maximize_container,
                close_container,
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.END,
        )
    def _minimize(self, e):
        self.page.window.minimized = True
        self.page.update()
    def _toggle_maximize(self, e):
        self.page.window.maximized = not self.page.window.maximized
        self.page.update()

        # アイコンとツールチップを切り替え
        if self.page.window.maximized:
            self.maximize_button.icon = ft.Icons.FULLSCREEN_EXIT
            self.maximize_button.tooltip = "元に戻す"
        else:
            self.maximize_button.icon = ft.Icons.FULLSCREEN
            self.maximize_button.tooltip = "最大化"
        self.maximize_button.update()
    def _close(self, e):
        # 設定保存はメイン側でやってるので、ここでは単に閉じるだけ
        self.page.window.close()
    def _on_hover_close(self, e: ft.HoverEvent):
        # ホバーで閉じるボタンを真っ赤に
        if e.data == "true":
            e.control.bgcolor = ft.Colors.RED
        else:
            e.control.bgcolor = ft.Colors.with_opacity(0.9, ft.Colors.RED)
        e.control.update()