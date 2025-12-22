import flet as ft

#右パネルの表示変更対象のタイトル文字列
RIGHT_PANEL_TITLES = ["ファイル情報", "PNG メタデータ", "Stealth PNG Info"]

class ThemeColors:
    @staticmethod
    def light():
        return {
            "bg_main": ft.Colors.WHITE70,
            "bg_panel": ft.Colors.WHITE,
            "text_primary": ft.Colors.BLACK,
            "text_secondary": ft.Colors.OUTLINE,
            "hover": ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            "selected": ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
            "surface": ft.Colors.SURFACE,
            "meta_secondary_title": ft.Colors.TEAL_900,
        }
    @staticmethod
    def dark():
        return {
            "bg_main": ft.Colors.with_opacity(0.98, "#0e0e0e"),
            "bg_panel": ft.Colors.with_opacity(0.96, "#121212"),
            "text_primary": ft.Colors.WHITE,
            "text_secondary": ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            "hover": ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            "selected": ft.Colors.with_opacity(0.22, ft.Colors.WHITE),
            "surface": ft.Colors.with_opacity(0.98, "#1e1e1e"),
            "meta_secondary_title": ft.Colors.TEAL_ACCENT_400,
        }

class ThemeManager:
    # 初期化
    def __init__(self, settings):
        self.settings = settings
        self.update_colors()
    ####################
    # カラーテーマ設定の更新
    ####################
    def update_colors(self):
        self.colors = ThemeColors.dark() if self.settings["settings"]["dark_theme"] else ThemeColors.light()
    ####################
    # アプリケーションにテーマを反映させる
    ####################
    def apply_to_app(self, page, left_panel, center_panel, right_panel):
        # テーマモード
        page.theme_mode = ft.ThemeMode.DARK if self.settings["settings"]["dark_theme"] else ft.ThemeMode.LIGHT
        # 背景色
        page.bgcolor = self.colors["bg_main"]
        if center_panel:
            center_panel.container.bgcolor = self.colors["bg_main"]
        if left_panel:
            left_panel.container.bgcolor = self.colors["bg_panel"]
        if right_panel:
            right_panel.container.bgcolor = self.colors["bg_panel"]
        # 現在パスの色
        if hasattr(page, "current_path_text"):
            page.current_path_text.color = self.colors["text_secondary"]
        # 右パネルのタイトル色を更新
        if right_panel and right_panel.metadata_text.controls:
            for ctrl in right_panel.metadata_text.controls:
                if isinstance(ctrl, ft.Text) and ctrl.value in RIGHT_PANEL_TITLES:
                    ctrl.color = self.colors["meta_secondary_title"]
        # ページ全体のアップデート
        page.update()