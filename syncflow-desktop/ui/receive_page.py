import flet as ft
import os
import platform
import subprocess
from pathlib import Path
from .theme import DSColor, DSSpacing, DSRadius
from server.storage import storage_manager

class ReceivePage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.content = self.build_ui()

    def build_ui(self):
        title_row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=DSSpacing.MD,
                    controls=[
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=DSRadius.ICON_BLOCK,
                            bgcolor=DSColor.SURFACE_HIGH,
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.icons.DOWNLOAD_ROUNDED, color=DSColor.PRIMARY, size=18),
                        ),
                        ft.Text("File nhận từ iPhone", size=24, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                    ]
                ),
                ft.ElevatedButton(
                    "Mở thư mục nhận",
                    icon=ft.icons.FOLDER_ROUNDED,
                    style=ft.ButtonStyle(
                        bgcolor=DSColor.PRIMARY,
                        color=ft.colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                        padding=ft.padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
                    ),
                    on_click=self.open_storage_folder,
                )
            ]
        )

        files = self.get_received_files()
        file_items = []
        if not files:
            empty_state = ft.Container(
                alignment=ft.alignment.center,
                padding=DSSpacing.XXXL,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=DSSpacing.MD,
                    controls=[
                        ft.Container(
                            width=64,
                            height=64,
                            border_radius=16,
                            bgcolor=DSColor.SURFACE_HIGH,
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.icons.INBOX_ROUNDED, color=DSColor.TEXT_MUTED, size=32),
                        ),
                        ft.Text("Chưa có file nào được chuyển đến", size=16, color=DSColor.TEXT_MUTED, weight=ft.FontWeight.W_500),
                        ft.Text("Khi iPhone gửi file lên, chúng sẽ xuất hiện tại đây và lưu vào thư mục Downloads/SyncFlow", size=13, color=DSColor.TEXT_MUTED),
                    ]
                )
            )
            file_items.append(empty_state)
        else:
            for p in files:
                file_items.append(self._build_file_row(p))

        self.file_column = ft.Column(spacing=DSSpacing.SM, controls=file_items)

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[
                title_row,
                ft.Text(f"ĐƯỜNG DẪN LƯU: {storage_manager.base_dir}", size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                self.file_column
            ]
        )

    def get_received_files(self):
        storage_dir = storage_manager.base_dir
        if not storage_dir.exists():
            return []
        items = []
        for item in sorted(storage_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if item.is_file() and not item.name.startswith("."):
                items.append(item)
        return items

    def _build_file_row(self, p: Path):
        size_mb = p.stat().st_size / (1024 * 1024)
        ext = p.suffix.lower()

        icon = ft.icons.INSERT_DRIVE_FILE_ROUNDED
        if ext in [".png", ".jpg", ".jpeg", ".heic", ".webp"]:
            icon = ft.icons.IMAGE_ROUNDED
        elif ext in [".mp4", ".mov", ".mkv", ".avi"]:
            icon = ft.icons.VIDEOCAM_ROUNDED
        elif ext in [".mp3", ".wav", ".m4a", ".flac"]:
            icon = ft.icons.AUDIO_FILE_ROUNDED
        elif ext in [".zip", ".tar", ".gz", ".rar", ".7z"]:
            icon = ft.icons.FOLDER_ZIP_ROUNDED

        return ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.MD,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=DSSpacing.MD,
                        controls=[
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=DSRadius.ICON_BLOCK,
                                bgcolor=DSColor.SURFACE_HIGH,
                                alignment=ft.alignment.center,
                                content=ft.Icon(icon, color=DSColor.PRIMARY, size=16),
                            ),
                            ft.Column(
                                spacing=DSSpacing.XS,
                                controls=[
                                    ft.Text(p.name, size=14, weight=ft.FontWeight.W_500, color=DSColor.TEXT_PRIMARY),
                                    ft.Text(f"{size_mb:.2f} MB", size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                                ]
                            )
                        ]
                    ),
                    ft.IconButton(
                        icon=ft.icons.OPEN_IN_NEW_ROUNDED,
                        icon_color=DSColor.PRIMARY,
                        tooltip="Mở file",
                        on_click=lambda _, path=p: self.open_file(path)
                    )
                ]
            )
        )

    def open_storage_folder(self, _):
        folder = str(storage_manager.base_dir)
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(folder)
            elif system == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass

    def open_file(self, path: Path):
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(str(path))
            elif system == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass
