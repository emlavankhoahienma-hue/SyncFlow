import flet as ft
from pathlib import Path
import shutil
from .theme import DSColor, DSSpacing, DSRadius
from server.storage import storage_manager

class SendPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.selected_files = []
        self.file_picker = ft.FilePicker()
        if hasattr(self.main_page, "overlay") and self.main_page.overlay is not None:
            self.main_page.overlay.append(self.file_picker)
        self.content = self.build_ui()

    def build_ui(self):
        title_row = ft.Row(
            spacing=DSSpacing.MD,
            controls=[
                ft.Container(
                    width=32,
                    height=32,
                    border_radius=DSRadius.ICON_BLOCK,
                    bgcolor=DSColor.SURFACE_HIGH,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(ft.Icons.UPLOAD_ROUNDED, color=DSColor.PRIMARY, size=18),
                ),
                ft.Text("Gửi file đến iPhone", size=24, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
            ]
        )

        # Drop/Select Area
        drop_area = ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            border=ft.Border.all(1, DSColor.BORDER),
            padding=DSSpacing.XXL,
            alignment=ft.Alignment(0, 0),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=DSSpacing.MD,
                controls=[
                    ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=48, color=DSColor.PRIMARY),
                    ft.Text("Kéo thả file vào đây hoặc chọn từ máy tính", size=16, weight=ft.FontWeight.W_500, color=DSColor.TEXT_PRIMARY),
                    ft.Text("Hỗ trợ mọi định dạng file (ảnh RAW, HEIC, video 4K, tài liệu, zip...)", size=13, color=DSColor.TEXT_MUTED),
                    ft.ElevatedButton(
                        "Chọn file để gửi",
                        icon=ft.Icons.FOLDER_OPEN,
                        style=ft.ButtonStyle(
                            bgcolor=DSColor.PRIMARY,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                            padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
                        ),
                        on_click=self.trigger_pick_files,
                    )
                ]
            )
        )

        self.queue_list = ft.Column(spacing=DSSpacing.SM)

        self.auto_convert_switch = ft.Switch(
            label="Tự động chuyển đổi định dạng (HEIC→PNG, HEVC→MP4 giữ CRF 18)",
            value=True,
            active_color=DSColor.PRIMARY,
        )

        self.share_btn = ft.ElevatedButton(
            "Đưa vào hàng đợi sẵn sàng cho iPhone tải",
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=DSColor.PRIMARY,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
            ),
            on_click=self.on_commit_share,
        )

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[
                title_row,
                drop_area,
                self.auto_convert_switch,
                ft.Text("DANH SÁCH FILE ĐÃ CHỌN", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                self.queue_list,
                self.share_btn
            ]
        )

    def trigger_pick_files(self, _):
        files = self.file_picker.pick_files(allow_multiple=True)
        if files:
            self.on_files_selected(files)

    def on_files_selected(self, files):
        if not files:
            return
        self.selected_files = [f.path for f in files if getattr(f, "path", None)]
        self.queue_list.controls.clear()

        for p_str in self.selected_files:
            p = Path(p_str)
            ext = p.suffix.lower()
            badge_text = None
            if ext in [".heic", ".heif"]:
                badge_text = "HEIC → PNG"
            elif ext in [".mov", ".hevc"]:
                badge_text = "MOV → MP4 (CRF 18)"

            size_mb = p.stat().st_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB"

            row = ft.Container(
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
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Icon(ft.Icons.INSERT_DRIVE_FILE_ROUNDED, color=DSColor.PRIMARY, size=16),
                                ),
                                ft.Column(
                                    spacing=DSSpacing.XS,
                                    controls=[
                                        ft.Text(p.name, size=14, weight=ft.FontWeight.W_500, color=DSColor.TEXT_PRIMARY),
                                        ft.Text(size_str, size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                                    ]
                                )
                            ]
                        ),
                        ft.Row(
                            spacing=DSSpacing.SM,
                            controls=[
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=DSSpacing.SM, vertical=DSSpacing.XS),
                                    border_radius=DSRadius.ICON_BLOCK,
                                    bgcolor=DSColor.SURFACE_HIGH,
                                    content=ft.Text(badge_text, size=11, color=DSColor.PRIMARY, weight=ft.FontWeight.W_600)
                                ) if badge_text else ft.Container(),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_color=DSColor.TEXT_MUTED,
                                    icon_size=16,
                                    on_click=lambda _, path=p_str: self.remove_file(path)
                                )
                            ]
                        )
                    ]
                )
            )
            self.queue_list.controls.append(row)

        self.share_btn.disabled = len(self.selected_files) == 0
        self.main_page.update()

    def remove_file(self, path: str):
        if path in self.selected_files:
            self.selected_files.remove(path)
        # re-render
        self.queue_list.controls = [c for c in self.queue_list.controls if getattr(c, "data", None) != path]
        self.share_btn.disabled = len(self.selected_files) == 0
        self.main_page.update()

    def on_commit_share(self, _):
        """Copies or links files into send_dir so /files exposes them to iPhone."""
        send_dir = storage_manager.send_dir
        for p_str in self.selected_files:
            src = Path(p_str)
            dst = send_dir / src.name
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

        self.selected_files.clear()
        self.queue_list.controls.clear()
        self.share_btn.disabled = True
        snack = ft.SnackBar(ft.Text("Đã thêm file vào hàng đợi chia sẻ! iPhone có thể tải về ngay.", color=ft.Colors.WHITE), bgcolor=DSColor.PRIMARY)
        self.main_page.overlay.append(snack)
        snack.open = True
        self.main_page.update()
