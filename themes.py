# pythonモジュール
import flet as ft

####################
# カラーテーマ定義
####################
class ThemeColors:
    @staticmethod
    def light():
        return {
            "bg_main": ft.Colors.WHITE,
            "bg_panel": ft.Colors.WHITE,
            "text_primary": ft.Colors.BLACK,
            "text_secondary": ft.Colors.OUTLINE,
            "divider": ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE),
            "hover": ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            "selected": ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
            "surface": ft.Colors.SURFACE,
            "meta_secondary_title": ft.Colors.TEAL_900,
        }
    @staticmethod
    def dark():
        return {
            "bg_main": ft.Colors.with_opacity(0.98, "#0e0e0e"),   # ほぼ真っ黒
            "bg_panel": ft.Colors.with_opacity(0.96, "#121212"),  # 少し明るめのカード
            "text_primary": ft.Colors.WHITE,
            "text_secondary": ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            "divider": ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            "hover": ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            "selected": ft.Colors.with_opacity(0.22, ft.Colors.WHITE),
            "surface": ft.Colors.with_opacity(0.98, "#1e1e1e"),
            "meta_secondary_title": ft.Colors.TEAL_ACCENT_400,
        }

####################
# テーマ変更処理
####################
def apply_theme(
        page: ft.Page, 
        settings: dict,
        left_panel: ft.Container, 
        center_panel: ft.Container, 
        right_panel: ft.Container,
        current_path_text: ft.Text,
        metadata_text: ft.Column,
        dir_list: ft.Column,
        theme_colors: dict
    ):
    theme_colors = ThemeColors.dark() if settings["dark_theme"] else ThemeColors.light()
    page.theme_mode = ft.ThemeMode.DARK if settings["dark_theme"] else ft.ThemeMode.LIGHT
    page.bgcolor = theme_colors["bg_main"]
    # 中央パネル
    center_panel.bgcolor = theme_colors["bg_main"]
    # 左パネル
    left_panel.bgcolor = theme_colors["bg_panel"]
    left_panel.border = ft.border.all(1, theme_colors["divider"])
    # 右パネル
    right_panel.bgcolor = theme_colors["bg_panel"]
    right_panel.border = ft.border.all(1, theme_colors["divider"])
    # 汎用テキスト系
    current_path_text.color = theme_colors["text_secondary"]
    for ctrl in page.controls:
        if isinstance(ctrl, ft.Row):
            for c in ctrl.controls:
                _walk_and_color(c, dir_list, theme_colors)
    # メタデータエリアの区切り線と固有のテキスト
    if metadata_text.controls:
        for c in metadata_text.controls:
            if isinstance(c, ft.Divider):
                c.color = theme_colors["divider"]
            if isinstance(c, ft.Text):
                # 変えないと見にくくなるものだけ変更
                if c.value == "PNG メタデータ" or c.value == "ファイル情報":
                    c.color = theme_colors["meta_secondary_title"]
    page.update()
def _walk_and_color(control, dir_list, theme_colors):
    """再帰的に色を適用（必要に応じて追加）"""
    if hasattr(control, "color") and control.color in (ft.Colors.BLACK, ft.Colors.WHITE, ft.Colors.OUTLINE):
        if isinstance(control, ft.Text):
            control.color = theme_colors["text_primary"] if control.weight == ft.FontWeight.BOLD else theme_colors["text_secondary"]
    if hasattr(control, "bgcolor"):
        if control == dir_list:
            return
        # ホバー用コンテナは別途処理
        if isinstance(control, ft.Container) and control.ink:
            pass
    if hasattr(control, "controls"):
        for child in control.controls:
            _walk_and_color(child)