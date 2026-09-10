import flet as ft
import io
import base64
from .theme import DSColor, DSSpacing, DSRadius
from server.discovery import BonjourServer
from server.security import crypto_manager

class HomePage(ft.Container):
    def __init__(self, page: ft.Page, on_navigate):
        super().__init__(expand=True)
        self.main_page = page
        self.on_navigate = on_navigate
        self.content = self.build_ui()

    def build_ui(self):
        # Header with Title, PIN Badge and Connection Status
        header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                            content=ft.Icon(ft.Icons.SYNC_ROUNDED, color=DSColor.PRIMARY, size=18),
                        ),
                        ft.Text(
                            "SyncFlow Desktop",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=DSColor.TEXT_PRIMARY,
                        ),
                    ]
                ),
                ft.Row(
                    spacing=DSSpacing.SM,
                    controls=[
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=DSSpacing.MD, vertical=DSSpacing.XS),
                            border_radius=12,
                            bgcolor=DSColor.SURFACE_HIGH,
                            content=ft.Row(
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=DSColor.PRIMARY, size=14),
                                    ft.Text(f"PIN: {crypto_manager.session_pin}", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                                ]
                            )
                        ),
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=DSSpacing.MD, vertical=DSSpacing.XS),
                            border_radius=12,
                            bgcolor=DSColor.SURFACE_HIGH,
                            content=ft.Row(
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Container(
                                        width=8,
                                        height=8,
                                        border_radius=4,
                                        bgcolor=DSColor.SUCCESS,
                                    ),
                                    ft.Text("Đang chạy", size=12, weight=ft.FontWeight.W_500, color=DSColor.TEXT_MUTED),
                                ]
                            )
                        )
                    ]
                )
            ]
        )

        self.active_status_label = ft.Text("Đang sẵn sàng", size=12, color=DSColor.PRIMARY, font_family="monospace")
        self.active_ring = ft.ProgressRing(width=48, height=48, stroke_width=5, value=0.0, color=DSColor.PRIMARY, bgcolor=DSColor.SURFACE_HIGH)
        self.active_title = ft.Text("Chưa có tác vụ nào", size=16, weight=ft.FontWeight.W_600, color=DSColor.TEXT_PRIMARY)
        self.active_subtitle = ft.Text("0 MB / 0 MB • 0.0 MB/s", size=13, font_family="monospace", color=DSColor.TEXT_MUTED)

        # TransferCard (The ONLY component with shadow allowed by Design System)
        self.active_card = ft.Container(
            border_radius=DSRadius.CARD,
            bgcolor=DSColor.SURFACE,
            padding=DSSpacing.XL,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color="#33000000",
                offset=ft.Offset(0, 4),
            ),
            content=ft.Column(
                spacing=DSSpacing.MD,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("TRUYỀN TẢI HIỆN TẠI", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                            self.active_status_label,
                        ]
                    ),
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=DSSpacing.LG,
                        controls=[
                            self.active_ring,
                            ft.Column(
                                spacing=DSSpacing.XS,
                                controls=[
                                    self.active_title,
                                    self.active_subtitle,
                                ]
                            )
                        ]
                    )
                ]
            )
        )

        # Action Buttons (PrimaryButton: Radius 10, Primary Color)
        btn_send = ft.ElevatedButton(
            "Gửi file tới iPhone",
            icon=ft.Icons.UPLOAD_FILE_ROUNDED,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=DSColor.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
            ),
            on_click=lambda _: self.on_navigate(1),
        )

        btn_receive = ft.OutlinedButton(
            "Xem thư mục nhận",
            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
            style=ft.ButtonStyle(
                color=DSColor.TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
                side=ft.BorderSide(width=0.5, color=DSColor.PRIMARY),
            ),
            on_click=lambda _: self.on_navigate(2),
        )

        btn_qr = ft.OutlinedButton(
            "Mã QR kết nối",
            icon=ft.Icons.QR_CODE_2_ROUNDED,
            style=ft.ButtonStyle(
                color=DSColor.PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=DSRadius.BUTTON),
                padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.MD),
                side=ft.BorderSide(width=1, color=DSColor.PRIMARY),
            ),
            on_click=self.show_qr_dialog,
        )

        quick_actions = ft.Row(
            spacing=DSSpacing.MD,
            controls=[btn_send, btn_receive, btn_qr]
        )

        # Recent activities
        recent_list = ft.Column(
            spacing=DSSpacing.SM,
            controls=[
                ft.Text("HOẠT ĐỘNG GẦN ĐÂY", size=12, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                ft.Container(
                    border_radius=DSRadius.CARD,
                    bgcolor=DSColor.SURFACE,
                    padding=DSSpacing.LG,
                    content=ft.Column(
                        spacing=DSSpacing.MD,
                        controls=[
                            self._build_recent_row("IMG_0241.png", "12.4 MB", "Đã nhận", ft.Icons.IMAGE_ROUNDED),
                            self._build_recent_row("Video_Demo.mp4", "184.2 MB", "Đã nhận", ft.Icons.VIDEOCAM_ROUNDED),
                        ]
                    )
                )
            ]
        )

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XXL,
            controls=[header, self.active_card, quick_actions, recent_list],
        )

    def _build_recent_row(self, name: str, size: str, status: str, icon_name):
        return ft.Row(
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
                            content=ft.Icon(icon_name, color=DSColor.PRIMARY, size=16),
                        ),
                        ft.Column(
                            spacing=DSSpacing.XS,
                            controls=[
                                ft.Text(name, size=14, weight=ft.FontWeight.W_500, color=DSColor.TEXT_PRIMARY),
                                ft.Text(size, size=12, font_family="monospace", color=DSColor.TEXT_MUTED),
                            ]
                        )
                    ]
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=DSSpacing.SM, vertical=DSSpacing.XS),
                    border_radius=DSRadius.ICON_BLOCK,
                    bgcolor=DSColor.SURFACE_HIGH,
                    content=ft.Text(status, size=11, color=DSColor.SUCCESS, weight=ft.FontWeight.W_500)
                )
            ]
        )

    def update_transfer(self, name: str, percent: float, sent_mb: float, total_mb: float, speed_mb: float, eta_s: float):
        self.active_status_label.value = "Đang truyền tải"
        self.active_status_label.color = DSColor.PRIMARY
        self.active_ring.value = percent
        self.active_title.value = name
        self.active_subtitle.value = f"{sent_mb:.2f} MB / {total_mb:.2f} MB • {speed_mb:.2f} MB/s (ETA: {int(eta_s)}s)"
        self.main_page.update()

    def mark_completed(self, name: str):
        self.active_status_label.value = "Hoàn tất"
        self.active_status_label.color = DSColor.SUCCESS
        self.active_ring.value = 1.0
        self.active_ring.color = DSColor.SUCCESS
        self.active_title.value = name
        self.active_subtitle.value = "Đã hoàn tất truyền tải"
        self.main_page.update()

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

    def show_qr_dialog(self, _=None):
        local_ip = BonjourServer.get_local_ip()

        def build_dialog_content():
            pin = crypto_manager.session_pin
            token = crypto_manager.pairing_token
            fingerprint = crypto_manager.get_server_fingerprint()
            server_url = f"http://{local_ip}:8765?pin={pin}&token={token}&fp={fingerprint}"
            qr_b64 = self.generate_qr(server_url)

            return ft.Container(
                width=360,
                padding=DSSpacing.MD,
                content=ft.Column(
                    main_axis_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=DSSpacing.MD,
                    tight=True,
                    controls=[
                        ft.Image(
                            src=f"data:image/png;base64,{qr_b64}",
                            width=220,
                            height=220,
                            fit=ft.BoxFit.CONTAIN,
                            border_radius=ft.BorderRadius.all(DSRadius.CARD),
                        ) if qr_b64 else ft.Text("QR Unavailable"),
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=DSSpacing.LG, vertical=DSSpacing.SM),
                            bgcolor=DSColor.SURFACE_HIGH,
                            border_radius=ft.BorderRadius.all(DSRadius.BUTTON),
                            border=ft.border.all(1, DSColor.PRIMARY),
                            content=ft.Row(
                                main_axis_alignment=ft.MainAxisAlignment.CENTER,
                                spacing=DSSpacing.SM,
                                controls=[
                                    ft.Icon(ft.Icons.LOCK_ROUNDED, size=16, color=DSColor.PRIMARY),
                                    ft.Text("MÃ PIN:", size=13, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_MUTED),
                                    ft.Text(pin, size=20, weight=ft.FontWeight.BOLD, color=DSColor.PRIMARY, font_family="monospace"),
                                ]
                            )
                        ),
                        ft.Text(f"IP: {local_ip}  •  Port: 8765  •  FP: {fingerprint}", size=13, weight=ft.FontWeight.BOLD, font_family="monospace", color=DSColor.TEXT_PRIMARY),
                        ft.Text("Mã PIN, Token & Khóa ECDH sinh ngẫu nhiên trên RAM. Chống MITM giả mạo & không lộ bất kỳ bí mật nào trên GitHub!", size=11, text_align=ft.TextAlign.CENTER, color=DSColor.TEXT_MUTED),
                    ]
                )
            )

        def on_regen_pin(_):
            crypto_manager.regenerate_secrets()
            dlg.content = build_dialog_content()
            self.content = self.build_ui()
            self.main_page.update()

        def close_dialog(_):
            dlg.open = False
            self.main_page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                spacing=DSSpacing.MD,
                controls=[
                    ft.Icon(ft.Icons.QR_CODE_ROUNDED, color=DSColor.PRIMARY, size=24),
                    ft.Text("Mã QR & PIN Bảo Vệ", size=18, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
                ]
            ),
            content=build_dialog_content(),
            actions=[
                ft.TextButton("Đổi mã PIN mới", on_click=on_regen_pin, style=ft.ButtonStyle(color=DSColor.TEXT_MUTED)),
                ft.TextButton("Đóng", on_click=close_dialog, style=ft.ButtonStyle(color=DSColor.PRIMARY)),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.main_page.dialog = dlg
        dlg.open = True
        self.main_page.update()

