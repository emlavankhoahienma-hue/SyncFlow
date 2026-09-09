import flet as ft
import io
import base64
from pathlib import Path
from .theme import DSColor, DSSpacing, DSRadius
from server.discovery import BonjourServer
from server.storage import storage_manager

class SettingsPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.local_ip = BonjourServer.get_local_ip()
        self.server_url = f"http://{self.local_ip}:8765"
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
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.icons.SETTINGS_ROUNDED, color=DSColor.PRIMARY, size=18),
                ),
                ft.Text("Cài đặt & Kết nối", size=24, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
            ]
        )

        # Connection Card with QR code
        qr_image_base64 = self.generate_qr(self.server_url)

        qr_control = ft.Image(
            src_base64=qr_image_base64,
            width=180,
            height=180,
            fit=ft.ImageFit.CONTAIN,
            border_radius=ft.border_radius.all(DSRadius.CARD),
        ) if qr_image_base64 else ft.Container(
            width=180,
            height=180,
            bgcolor=DSColor.SURFACE_HIGH,
            border_radius=DSRadius.CARD,
            alignment=ft.alignment.center,
            content=ft.Text("QR Unavailable", color=DSColor.TEXT_MUTED)
        )

        connection_card = ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.XL,
            content=ft.Row(
                spacing=DSSpacing.XXL,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    qr_control,
                    ft.Column(
                        spacing=DSSpacing.MD,
                        expand=True,
                        controls=[
                            ft.Text("QUÉT ĐỂ KẾT NỐI TỪ IPHONE", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                            ft.Row(
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Text("Địa chỉ IP:", size=14, color=DSColor.TEXT_MUTED),
                                    ft.Text(self.local_ip, size=16, weight=ft.FontWeight.BOLD, font_family="monospace", color=DSColor.PRIMARY),
                                ]
                            ),
                            ft.Row(
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Text("Cổng dịch vụ:", size=14, color=DSColor.TEXT_MUTED),
                                    ft.Text("8765", size=16, weight=ft.FontWeight.BOLD, font_family="monospace", color=DSColor.TEXT_PRIMARY),
                                ]
                            ),
                            ft.Row(
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Text("URL đầy đủ:", size=14, color=DSColor.TEXT_MUTED),
                                    ft.Text(self.server_url, size=14, font_family="monospace", color=DSColor.TEXT_PRIMARY),
                                ]
                            ),
                            ft.Text("Mở SyncFlow trên iPhone, chọn mục Cài đặt và nhập IP trên hoặc app sẽ tự động tìm thấy máy tính qua Bonjour/mDNS.", size=13, color=DSColor.TEXT_MUTED),
                        ]
                    )
                ]
            )
        )

        # Storage Path Card
        self.txt_storage = ft.TextField(
            value=str(storage_manager.base_dir),
            label="Thư mục lưu file nhận",
            read_only=True,
            border_color=DSColor.BORDER,
            focused_border_color=DSColor.PRIMARY,
            text_size=13,
            text_style=ft.TextStyle(font_family="monospace"),
            expand=True,
        )

        storage_card = ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.XL,
            content=ft.Column(
                spacing=DSSpacing.MD,
                controls=[
                    ft.Text("VỊ TRÍ LƯU TRỮ", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                    ft.Row(
                        spacing=DSSpacing.MD,
                        controls=[
                            self.txt_storage,
                        ]
                    ),
                    ft.Text("Mọi file gửi từ iPhone sẽ được lưu trực tiếp vào thư mục này.", size=13, color=DSColor.TEXT_MUTED),
                ]
            )
        )

        # About Card
        about_card = ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.XL,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=DSSpacing.XS,
                        controls=[
                            ft.Text("SyncFlow Desktop Ecosystem", size=16, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                            ft.Text("FastAPI + Flet • Sideload Companion for iPhone", size=13, color=DSColor.TEXT_MUTED),
                        ]
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=DSSpacing.MD, vertical=DSSpacing.XS),
                        border_radius=DSRadius.ICON_BLOCK,
                        bgcolor=DSColor.SURFACE_HIGH,
                        content=ft.Text("v1.0.0", size=12, font_family="monospace", color=DSColor.PRIMARY, weight=ft.FontWeight.BOLD)
                    )
                ]
            )
        )

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[title_row, connection_card, storage_card, about_card]
        )

    def generate_qr(self, data: str) -> str:
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:
            return ""
