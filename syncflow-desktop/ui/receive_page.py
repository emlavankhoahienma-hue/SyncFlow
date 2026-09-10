import flet as ft
import os
import platform
import subprocess
import logging
from pathlib import Path
from .theme import DSColor, DSSpacing, DSRadius
from server.storage import storage_manager

logger = logging.getLogger("syncflow.receive_page")

class ReceivePage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.file_column = ft.Column(spacing=DSSpacing.SM)
        self.content = self.build_ui()

    def show_message(self, message: str, is_error: bool = False):
        if not self.main_page:
            return
        try:
            snack = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE, size=13),
                bgcolor=ft.Colors.RED_700 if is_error else DSColor.SURFACE_HIGH,
                duration=3500,
            )
            self.main_page.show_dialog(snack)
        except Exception:
            pass

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
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color=DSColor.PRIMARY, size=18),
                        ),
                        ft.Text("File nhận từ iPhone", size=24, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                    ]
                ),
                ft.Row(
                    spacing=DSSpacing.SM,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_color=DSColor.PRIMARY,
                            tooltip="Làm mới danh sách file",
                            on_click=lambda _: self.refresh_files(),
                        ),
                        ft.ElevatedButton(
                            "Mở thư mục nhận",
                            icon=ft.Icons.FOLDER_ROUNDED,
                            style=ft.ButtonStyle(
                                bgcolor=DSColor.PRIMARY,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
                            ),
                            on_click=self.open_storage_folder,
                        )
                    ]
                )
            ]
        )

        self._populate_files()

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[
                title_row,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"ĐƯỜNG DẪN LƯU: {storage_manager.base_dir}", size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                    ]
                ),
                self.file_column
            ]
        )

    def _build_empty_state(self):
        return ft.Container(
            alignment=ft.Alignment(0, 0),
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
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.INBOX_ROUNDED, color=DSColor.TEXT_MUTED, size=32),
                    ),
                    ft.Text("Chưa có file nào được chuyển đến", size=16, color=DSColor.TEXT_MUTED, weight=ft.FontWeight.W_500),
                    ft.Text("Khi iPhone gửi file lên, chúng sẽ xuất hiện tại đây và lưu vào thư mục Downloads/SyncFlow", size=13, color=DSColor.TEXT_MUTED),
                ]
            )
        )

    def _populate_files(self):
        files = self.get_received_files()
        file_items = []
        if not files:
            file_items.append(self._build_empty_state())
        else:
            for p in files:
                file_items.append(self._build_file_row(p))
        self.file_column.controls = file_items

    def refresh_files(self):
        self._populate_files()
        if self.main_page:
            try:
                self.file_column.update()
            except Exception:
                pass

    def get_received_files(self):
        storage_dir = storage_manager.base_dir
        if not storage_dir.exists():
            return []
        items = []
        try:
            for item in sorted(storage_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if item.is_file() and not item.name.startswith("."):
                    items.append(item)
        except Exception as e:
            logger.error(f"Error reading received files: {e}")
        return items

    def _build_file_row(self, p: Path):
        try:
            size_mb = p.stat().st_size / (1024 * 1024)
        except Exception:
            size_mb = 0.0

        ext = p.suffix.lower()
        icon = ft.Icons.INSERT_DRIVE_FILE_ROUNDED
        if ext in [".png", ".jpg", ".jpeg", ".heic", ".webp", ".gif"]:
            icon = ft.Icons.IMAGE_ROUNDED
        elif ext in [".mp4", ".mov", ".mkv", ".avi"]:
            icon = ft.Icons.VIDEOCAM_ROUNDED
        elif ext in [".mp3", ".wav", ".m4a", ".flac", ".aac"]:
            icon = ft.Icons.AUDIO_FILE_ROUNDED
        elif ext in [".zip", ".tar", ".gz", ".rar", ".7z"]:
            icon = ft.Icons.FOLDER_ZIP_ROUNDED

        return ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.MD,
            ink=True,
            on_click=lambda _, path=p: self.reveal_file_in_folder(path),
            tooltip=f"Bấm để mở vị trí: {p.name}",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=DSSpacing.MD,
                        controls=[
                            ft.Container(
                                width=36,
                                height=36,
                                border_radius=DSRadius.ICON_BLOCK,
                                bgcolor=DSColor.SURFACE_HIGH,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(icon, color=DSColor.PRIMARY, size=18),
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
                    ft.Row(
                        spacing=DSSpacing.XS,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                                icon_color=DSColor.PRIMARY,
                                tooltip="Mở vị trí file (Explorer)",
                                on_click=lambda _, path=p: self.reveal_file_in_folder(path),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                icon_color=DSColor.PRIMARY,
                                tooltip="Mở file trực tiếp",
                                on_click=lambda _, path=p: self.open_file(path),
                            ),
                        ]
                    )
                ]
            )
        )

    def reveal_file_in_folder(self, path: Path):
        try:
            resolved_path = Path(path).resolve()
            if not resolved_path.exists():
                self.show_message(f"Không tìm thấy file: {resolved_path.name}", is_error=True)
                return

            system = platform.system()
            if system == "Windows":
                # explorer.exe /select,"path" focuses and selects the file in Explorer
                subprocess.Popen(['explorer.exe', f'/select,{str(resolved_path)}'])
            elif system == "Darwin":
                subprocess.Popen(["open", "-R", str(resolved_path)])
            else:
                subprocess.Popen(["xdg-open", str(resolved_path.parent)])

            self.show_message(f"Đã mở vị trí: {resolved_path.name}")
        except Exception as e:
            logger.error(f"Error revealing file {path}: {e}")
            self.show_message(f"Lỗi mở vị trí file: {e}", is_error=True)

    def open_file(self, path: Path):
        try:
            resolved_path = Path(path).resolve()
            if not resolved_path.exists():
                self.show_message(f"File không tồn tại: {resolved_path.name}", is_error=True)
                return

            system = platform.system()
            if system == "Windows":
                try:
                    os.startfile(str(resolved_path))
                    self.show_message(f"Đang mở file: {resolved_path.name}")
                except OSError as err:
                    logger.warning(f"os.startfile failed for {resolved_path.name}: {err}. Opening OpenAs / Explorer.")
                    # If Windows doesn't have an associated app (e.g. m4a), prompt "Open With" dialog
                    try:
                        subprocess.Popen(f'rundll32.exe shell32.dll,OpenAs_RunDLL "{str(resolved_path)}"', shell=True)
                        self.show_message(f"Chưa có app mặc định. Đang mở hộp thoại chọn ứng dụng cho: {resolved_path.name}")
                    except Exception:
                        self.reveal_file_in_folder(resolved_path)
            elif system == "Darwin":
                subprocess.Popen(["open", str(resolved_path)])
                self.show_message(f"Đang mở file: {resolved_path.name}")
            else:
                subprocess.Popen(["xdg-open", str(resolved_path)])
                self.show_message(f"Đang mở file: {resolved_path.name}")
        except Exception as e:
            logger.error(f"Error opening file {path}: {e}")
            self.show_message(f"Lỗi mở file: {e}", is_error=True)

    def open_storage_folder(self, _=None):
        try:
            folder = storage_manager.base_dir.resolve()
            folder.mkdir(parents=True, exist_ok=True)
            system = platform.system()
            if system == "Windows":
                subprocess.Popen(['explorer.exe', str(folder)])
            elif system == "Darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self.show_message(f"Đã mở thư mục: {folder.name}")
        except Exception as e:
            logger.error(f"Error opening folder: {e}")
            self.show_message(f"Lỗi mở thư mục: {e}", is_error=True)

