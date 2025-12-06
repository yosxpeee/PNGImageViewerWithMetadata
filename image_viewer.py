# image_viewer_flet.py
import flet as ft
import os
from pathlib import Path
import string
import png
from datetime import datetime

def make_copyable_text(value: str, size=12):
    return ft.TextField(
        value=value,
        read_only=True,
        multiline=True,
        border="none",
        text_size=size,
        min_lines=1,
        max_lines=100,
    )

def main(page: ft.Page):
    page.title = "PNG Image Viewer"
    page.window_width  = 1440
    page.window_height = 900
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.padding = 0

    # ── 右ペイン：メタデータ ──
    metadata_text = ft.Column([ft.Text("画像を選択してください", size=18)], scroll=ft.ScrollMode.AUTO, expand=True)

    def update_metadata(image_path: str):
        metadata_text.controls.clear()
        if not image_path:
            metadata_text.controls.append(ft.Text("画像を選択してください"))
            page.update()
            return

        try:
            stat = os.stat(image_path)
            size_kb = stat.st_size / 1024

            metadata_text.controls.extend([
                ft.Text("ファイル情報", weight=ft.FontWeight.BOLD, size=12),
                ft.Divider(height=1),
                ft.Text(f"名前: {Path(image_path).name}"),
                ft.Text(f"サイズ: {size_kb:.1f} KB"),
                ft.Text(f"更新日時: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y/%m/%d %H:%M')}"),
                ft.Divider(height=1),
                ft.Text("PNG メタデータ", weight=ft.FontWeight.BOLD, size=12),
                ft.Divider(height=1),
            ])

            # tEXt / zTXt / iTXt
            with open(image_path, "rb") as f:
                reader = png.Reader(file=f)
                for chunk_type, data in reader.chunks():
                    ctype = chunk_type.decode("latin1", errors="ignore")
                    if ctype == "tEXt":
                        text = data.decode("latin1", errors="ignore")
                        if "::" in text:
                            k, v = text.split("::", 1)
                            metadata_text.controls.append(ft.Text(f"{k}: {v}"))
                        else:
                            #stable diffusionで作られた画像に特化したつくりにする
                            #print(text)
                            positive_index = text.find('parameters')
                            negative_index = text.find('Negative prompt: ')
                            anothers_index = text.find('Steps: ')
                            if positive_index != -1:
                                #print(positive_index)
                                #print(negative_index)
                                #print(anothers_index)
                                metadata_text.controls.append(make_copyable_text(f"<Prompt>\n{text[positive_index+11:negative_index].strip()}"))
                                metadata_text.controls.append(make_copyable_text(f"<Negative Prompt>\n{text[negative_index+17:anothers_index].strip()}"))
                                metadata_text.controls.append(make_copyable_text(f"<Other info>\nSteps: {text[anothers_index+7:].strip().replace(", ","\n")}"))
                            else:
                                metadata_text.controls.append(ft.Text(f"tEXt:\n{text}"))
                    elif ctype in ("iTXt", "zTXt"):
                        metadata_text.controls.append(ft.Text(f"{ctype}: あり"))

            # IHDR（画像サイズなど）
            reader = png.Reader(filename=image_path)
            w, h, _, info = reader.read()
            metadata_text.controls.extend([
                ft.Divider(height=1),
                ft.Text("画像情報", weight=ft.FontWeight.BOLD, size=12),
                ft.Divider(height=1),
                ft.Text(f"幅 × 高さ: {w} × {h} px"),
                ft.Text(f"ビット深度: {info.get('bitdepth')}"),
                ft.Text(f"透明度: {'あり' if info.get('alpha') else 'なし'}"),
            ])
        except Exception as e:
            metadata_text.controls.append(ft.Text(f"エラー: {e}", color="red"))
        page.update()

    # ── 中央：画像表示 ──
    image_view = ft.Image(
        src="", 
        fit=ft.ImageFit.CONTAIN, 
        expand=True
    )

    # ── 左ペイン ──
    current_path_text = ft.Text("", size=12, italic=True, color=ft.Colors.OUTLINE)
    dir_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 高さ調整可能＆ホバーエフェクトの汎用アイテム生成（Flet 0.28.3）
    def make_item(name: str, icon, path: str, is_folder=False):
        container = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=12),
                ft.Text(name, expand=True, size=12),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=12, opacity=0.5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            height=24,
            padding=ft.padding.symmetric(horizontal=1, vertical=1),
            border_radius=8,
            ink=True,
            on_click=lambda e: refresh_directory(path) if is_folder else select_image(path),
        )

        def hover(e):
            container.bgcolor = ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE) if e.data == "true" else None
            container.update()
        container.on_hover = hover
        return container

    def refresh_directory(path: str):
        dir_list.controls.clear()
        current_path_text.value = f"現在: {path}"
        p = Path(path)

        # ドライブ一覧に戻る
        back = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.COMPUTER, size=12),
                ft.Text("ドライブ一覧に戻る", expand=True, size=12),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=12, opacity=0.5),
            ]),
            height=24,
            padding=ft.padding.symmetric(horizontal=1, vertical=1),
            border_radius=8,
            ink=True,
            on_click=lambda e: show_drives(),
        )
        def h(e):
            back.bgcolor = ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY) if e.data == "true" else None
            back.update()
        back.on_hover = h
        dir_list.controls.append(back)
        dir_list.controls.append(ft.Divider(height=1))

        # 親フォルダ
        if p.parent != p and str(p.parent) != p.drive + "\\":
            dir_list.controls.append(make_item(".. (親フォルダ)", ft.Icons.ARROW_BACK, str(p.parent), True))

        try:
            for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    dir_list.controls.append(make_item(item.name + "/", ft.Icons.FOLDER, str(item), True))
                elif item.suffix.lower() == ".png":
                    dir_list.controls.append(make_item(item.name, ft.Icons.IMAGE, str(item), False))
        except PermissionError:
            dir_list.controls.append(ft.Text("アクセス拒否", color="red"))

        page.update()

    def select_image(path: str):
        image_view.src = path
        update_metadata(path)
        page.update()

    def show_drives():
        dir_list.controls.clear()
        current_path_text.value = "ドライブを選択してください"

        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    import win32api
                    label = win32api.GetVolumeInformation(drive)[0] or "ドライブ"
                except:
                    label = "ドライブ"
                dir_list.controls.append(make_item(f"{drive} [{label}]", ft.Icons.STORAGE, drive, True))
        page.update()

    # 起動時にドライブ一覧表示
    show_drives()

    # ── 最終レイアウト（サイドパネル真っ白）──
    page.add(
        ft.Row([
            # 左：白背景
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.EXPLORE), ft.Text("ファイルブラウザ", weight=ft.FontWeight.BOLD)]),
                    current_path_text,
                    ft.Divider(height=1),
                    dir_list,
                ], expand=True),
                bgcolor=ft.Colors.WHITE,
                padding=10,
                width=340,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            ),
            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),

            # 中央：画像
            ft.Container(image_view, alignment=ft.alignment.center, expand=2),

            ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE_VARIANT),

            # 右：白背景メタデータ
            ft.Container(
                content=ft.Column([
                    ft.Text("メタデータ", weight=ft.FontWeight.BOLD, size=18),
                    ft.Divider(height=1),
                    metadata_text,
                ], expand=True),
                bgcolor=ft.Colors.WHITE,
                padding=15,
                width=400,
                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
            ),
        ], expand=True)
    )

ft.app(target=main)