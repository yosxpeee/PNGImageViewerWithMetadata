import flet as ft


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
            "bg_main": ft.Colors.with_opacity(0.98, "#0e0e0e"),
            "bg_panel": ft.Colors.with_opacity(0.96, "#121212"),
            "text_primary": ft.Colors.WHITE,
            "text_secondary": ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
            "divider": ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
            "hover": ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
            "selected": ft.Colors.with_opacity(0.22, ft.Colors.WHITE),
            "surface": ft.Colors.with_opacity(0.98, "#1e1e1e"),
            "meta_secondary_title": ft.Colors.TEAL_ACCENT_400,
        }


class ThemeManager:
    def __init__(self, settings):
        self.settings = settings
        self.colors = ThemeColors.dark() if settings["dark_theme"] else ThemeColors.light()

    def toggle_theme(self):
        self.settings["dark_theme"] = not self.settings["dark_theme"]
        self.colors = ThemeColors.dark() if self.settings["dark_theme"] else ThemeColors.light()

    def apply_theme(self, page, left_panel, center_panel, right_panel):
        page.theme_mode = ft.ThemeMode.DARK if self.settings["dark_theme"] else ft.ThemeMode.LIGHT
        page.bgcolor = self.colors["bg_main"]

        if center_panel:
            center_panel.container.bgcolor = self.colors["bg_main"]
        if left_panel:
            left_panel.container.bgcolor = self.colors["bg_panel"]
            left_panel.container.border = ft.border.all(1, self.colors["divider"])
        if right_panel:
            right_panel.container.bgcolor = self.colors["bg_panel"]
            right_panel.container.border = ft.border.all(1, self.colors["divider"])

        # テキスト色適用など（再帰関数で）
        self._apply_colors_to_controls(page.controls, self.colors)

    def _apply_colors_to_controls(self, controls, colors):
        for control in controls:
            if isinstance(control, ft.Text):
                control.color = colors["text_primary"] if control.weight == ft.FontWeight.BOLD else colors["text_secondary"]
            if hasattr(control, "controls"):
                self._apply_colors_to_controls(control.controls, colors)