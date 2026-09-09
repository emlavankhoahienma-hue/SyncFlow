import flet as ft
from pathlib import Path
import shutil
import threading
import os
import platform
import subprocess
from .theme import DSColor, DSSpacing, DSRadius
from server.storage import storage_manager

class SendPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.selected_files = []
        self.content = self.build_ui()
        self.refresh_shared_files()

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

        # Status / Feedback Banner
        self.status_banner = ft.Container(
            visible=False,
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            border=ft.Border.all(1, DSColor.SUCCESS),
            padding=DSSpacing.MD,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=DSSpacing.MD,
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=DSColor.SUCCESS, size=24),
                            ft.Column(
                                spacing=DSSpacing.XS,
                                controls=[
                                    ft.Text("Đã đưa tệp vào hàng đợi chia sẻ thành công!", weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                                    ft.Text("Mở iPhone vào tab Nhận để tải về ngay lập tức.", size=12, color=DSColor.TEXT_MUTED)
                                ]
                            )
                        ]
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=18,
                        icon_color=DSColor.TEXT_MUTED,
                        on_click=lambda _: self.hide_banner()
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

        # Commit button with loading indicator support
        self.btn_progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE, visible=False)
        self.btn_text = ft.Text("Đưa vào hàng đợi sẵn sàng cho iPhone tải", color=ft.Colors.WHITE, weight=ft.FontWeight.W_600)
        self.btn_icon = ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.WHITE, size=18)

        self.share_btn = ft.ElevatedButton(
            content=ft.Row(
                tight=True,
                spacing=DSSpacing.SM,
                controls=[
                    self.btn_icon,
                    self.btn_progress_ring,
                    self.btn_text
                ]
            ),
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=DSColor.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
            ),
            on_click=self.on_commit_share,
        )

        # Section 2: Shared Files currently active in SendQueue
        self.shared_files_column = ft.Column(spacing=DSSpacing.SM)
        self.shared_files_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=DSSpacing.SM,
                    controls=[
                        ft.Text("TỆP ĐANG SẴN SÀNG CHO IPHONE TẢI", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                        self.make_badge("0 tệp", DSColor.SURFACE_HIGH, DSColor.PRIMARY)
                    ]
                ),
                ft.TextButton(
                    "Mở thư mục hàng đợi",
                    icon=ft.Icons.FOLDER_SPECIAL_ROUNDED,
                    style=ft.ButtonStyle(color=DSColor.PRIMARY),
                    on_click=self.open_send_folder,
                )
            ]
        )

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[
                title_row,
                self.status_banner,
                drop_area,
                self.auto_convert_switch,
                ft.Text("DANH SÁCH FILE ĐÃ CHỌN ĐỂ GỬI", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                self.queue_list,
                self.share_btn,
                ft.Divider(height=1, color=DSColor.BORDER),
                self.shared_files_header,
                self.shared_files_column
            ]
        )

    def hide_banner(self):
        self.status_banner.visible = False
        self.main_page.update()

    def make_badge(self, text, bg, fg):
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=DSSpacing.SM, vertical=DSSpacing.XS),
            border_radius=DSRadius.ICON_BLOCK,
            bgcolor=bg,
            content=ft.Text(text, size=11, color=fg, weight=ft.FontWeight.W_600)
        )

    def trigger_pick_files(self, _):
        def _pick():
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                paths = filedialog.askopenfilenames(
                    title="Chọn file để gửi tới iPhone",
                    filetypes=[("All Files (*.*)", "*.*")]
                )
                root.destroy()
                if paths:
                    self.on_files_selected(list(paths))
            except Exception:
                pass
        threading.Thread(target=_pick, daemon=True).start()

    def on_files_selected(self, paths):
        if not paths:
            return
        self.selected_files = [str(p) for p in paths]
        self.queue_list.controls.clear()
        self.hide_banner()

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
                data=p_str,
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
                                self.make_badge(badge_text, DSColor.SURFACE_HIGH, DSColor.PRIMARY) if badge_text else ft.Container(),
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
        self.btn_text.value = f"Đưa {len(self.selected_files)} tệp vào hàng đợi cho iPhone tải"
        self.main_page.update()

    def remove_file(self, path: str):
        if path in self.selected_files:
            self.selected_files.remove(path)
        self.queue_list.controls = [c for c in self.queue_list.controls if getattr(c, "data", None) != path]
        self.share_btn.disabled = len(self.selected_files) == 0
        if self.selected_files:
            self.btn_text.value = f"Đưa {len(self.selected_files)} tệp vào hàng đợi cho iPhone tải"
        else:
            self.btn_text.value = "Đưa vào hàng đợi sẵn sàng cho iPhone tải"
        self.main_page.update()

    def on_commit_share(self, _):
        """Copies files into send_dir in a background thread with visual feedback."""
        if not self.selected_files:
            return

        # 1. Update UI to processing state
        self.share_btn.disabled = True
        self.btn_icon.visible = False
        self.btn_progress_ring.visible = True
        self.btn_text.value = f"Đang chuẩn bị {len(self.selected_files)} tệp..."
        self.main_page.update()

        def _worker():
            send_dir = storage_manager.send_dir
            copied_count = 0
            for p_str in list(self.selected_files):
                src = Path(p_str)
                dst = send_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    copied_count += 1
                except Exception:
                    pass

            self.selected_files.clear()

            def _finish():
                self.queue_list.controls.clear()
                self.btn_progress_ring.visible = False
                self.btn_icon.visible = True
                self.btn_text.value = "Đưa vào hàng đợi sẵn sàng cho iPhone tải"
                self.share_btn.disabled = True

                # Show Success Banner
                self.status_banner.visible = True

                # Show SnackBar toast safely
                try:
                    snack = ft.SnackBar(
                        content=ft.Text(f"Đã đưa {copied_count} tệp vào hàng đợi chia sẻ thành công!", color=ft.Colors.WHITE),
                        bgcolor=DSColor.PRIMARY,
                        duration=3000
                    )
                    if hasattr(self.main_page, "open"):
                        self.main_page.open(snack)
                    elif hasattr(self.main_page, "snack_bar"):
                        self.main_page.snack_bar = snack
                        self.main_page.snack_bar.open = True
                except Exception:
                    pass

                self.refresh_shared_files()
                self.main_page.update()

            # Schedule UI update on page thread
            try:
                if hasattr(self.main_page, "run_thread"):
                    self.main_page.run_thread(_finish)
                else:
                    _finish()
            except Exception:
                _finish()

        threading.Thread(target=_worker, daemon=True).start()

    def refresh_shared_files(self):
        send_dir = storage_manager.send_dir
        if not send_dir.exists():
            send_dir.mkdir(parents=True, exist_ok=True)

        files = [p for p in sorted(send_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True) if p.is_file() and not p.name.startswith(".")]

        # Update count badge in header
        self.shared_files_header.controls[0].controls[1] = self.make_badge(f"{len(files)} tệp", DSColor.SURFACE_HIGH, DSColor.PRIMARY)

        self.shared_files_column.controls.clear()
        if not files:
            empty = ft.Container(
                alignment=ft.Alignment(0, 0),
                padding=DSSpacing.LG,
                content=ft.Text("Chưa có tệp nào trong hàng đợi chia sẻ.", size=13, color=DSColor.TEXT_MUTED)
            )
            self.shared_files_column.controls.append(empty)
        else:
            for p in files:
                size_mb = p.stat().st_size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB"
                p_path = str(p)

                card = ft.Container(
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
                                        content=ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=DSColor.SUCCESS, size=16),
                                    ),
                                    ft.Column(
                                        spacing=DSSpacing.XS,
                                        controls=[
                                            ft.Text(p.name, size=14, weight=ft.FontWeight.W_500, color=DSColor.TEXT_PRIMARY),
                                            ft.Text(f"{size_str} • Sẵn sàng", size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                                        ]
                                    )
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                                icon_color=DSColor.WARNING,
                                tooltip="Xóa khỏi hàng đợi chia sẻ",
                                on_click=lambda _, target=p_path: self.delete_shared_file(target)
                            )
                        ]
                    )
                )
                self.shared_files_column.controls.append(card)

    def delete_shared_file(self, path_str: str):
        try:
            p = Path(path_str)
            if p.exists():
                p.unlink()
        except Exception:
            pass
        self.refresh_shared_files()
        self.main_page.update()

    def open_send_folder(self, _):
        folder = str(storage_manager.send_dir)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass
