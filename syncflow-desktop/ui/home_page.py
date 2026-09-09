import flet as ft
from .theme import DSColor, DSSpacing, DSRadius

class HomePage(ft.Container):
    def __init__(self, page: ft.Page, on_navigate):
        super().__init__(expand=True)
        self.main_page = page
        self.on_navigate = on_navigate
        self.content = self.build_ui()

    def build_ui(self):
        # Header with Title and Connection Status
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
                            ft.Text(
                                "Đang chạy (:8765)",
                                size=12,
                                weight=ft.FontWeight.W_500,
                                color=DSColor.SUCCESS,
                                font_family="monospace"
                            ),
                        ]
                    )
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

        quick_actions = ft.Row(
            spacing=DSSpacing.MD,
            controls=[btn_send, btn_receive]
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
