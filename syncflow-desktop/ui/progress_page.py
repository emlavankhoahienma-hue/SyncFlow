import flet as ft
from .theme import DSColor, DSSpacing, DSRadius

class ProgressPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.transfers_map = {}
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
                    content=ft.Icon(ft.icons.TIMELAPSE_ROUNDED, color=DSColor.PRIMARY, size=18),
                ),
                ft.Text("Tiến độ truyền tải", size=24, weight=ft.FontWeight.BOLD, color=DSColor.TEXT_PRIMARY),
            ]
        )

        self.transfers_container = ft.Column(spacing=DSSpacing.LG)
        self.empty_label = ft.Container(
            alignment=ft.alignment.center,
            padding=DSSpacing.XXXL,
            content=ft.Text("Không có tác vụ nào đang truyền", size=14, color=DSColor.TEXT_MUTED)
        )
        self.transfers_container.controls.append(self.empty_label)

        return ft.ListView(
            padding=DSSpacing.XXL,
            spacing=DSSpacing.XL,
            controls=[title_row, self.transfers_container]
        )

    def update_progress(self, transfer_id: str, sent: int, total: int, speed_bps: float, eta_s: float):
        percent = (sent / total) if total > 0 else 0.0
        sent_mb = sent / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        speed_mb = speed_bps / (1024 * 1024)

        if transfer_id not in self.transfers_map:
            if self.empty_label in self.transfers_container.controls:
                self.transfers_container.controls.remove(self.empty_label)

            # Build UI block for transfer
            ring = ft.ProgressRing(width=56, height=56, stroke_width=6, value=percent, color=DSColor.PRIMARY, bgcolor=DSColor.SURFACE_HIGH)
            bar = ft.ProgressBar(value=percent, color=DSColor.PRIMARY, bgcolor=DSColor.SURFACE_HIGH, height=6)
            txt_percent = ft.Text(f"{percent * 100:.1f}%", size=20, weight=ft.FontWeight.BOLD, font_family="monospace", color=DSColor.TEXT_PRIMARY)
            txt_speed = ft.Text(f"{speed_mb:.2f} MB/s", size=14, font_family="monospace", color=DSColor.PRIMARY)
            txt_bytes = ft.Text(f"{sent_mb:.2f} MB / {total_mb:.2f} MB", size=13, font_family="monospace", color=DSColor.TEXT_MUTED)
            txt_eta = ft.Text(f"ETA: {int(eta_s)}s", size=13, font_family="monospace", color=DSColor.TEXT_MUTED)

            card = ft.Container(
                border_radius=DSRadius.CARD,
                bgcolor=DSColor.SURFACE,
                padding=DSSpacing.LG,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color="#20000000",
                    offset=ft.Offset(0, 4)
                ),
                content=ft.Column(
                    spacing=DSSpacing.MD,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Row(
                                    spacing=DSSpacing.MD,
                                    controls=[
                                        ring,
                                        ft.Column(
                                            spacing=DSSpacing.XS,
                                            controls=[
                                                txt_percent,
                                                txt_bytes,
                                            ]
                                        )
                                    ]
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    spacing=DSSpacing.XS,
                                    controls=[
                                        txt_speed,
                                        txt_eta,
                                    ]
                                )
                            ]
                        ),
                        bar,
                    ]
                )
            )

            self.transfers_map[transfer_id] = {
                "card": card,
                "ring": ring,
                "bar": bar,
                "txt_percent": txt_percent,
                "txt_speed": txt_speed,
                "txt_bytes": txt_bytes,
                "txt_eta": txt_eta
            }
            self.transfers_container.controls.append(card)
        else:
            t = self.transfers_map[transfer_id]
            t["ring"].value = percent
            t["bar"].value = percent
            t["txt_percent"].value = f"{percent * 100:.1f}%"
            t["txt_speed"].value = f"{speed_mb:.2f} MB/s"
            t["txt_bytes"].value = f"{sent_mb:.2f} MB / {total_mb:.2f} MB"
            t["txt_eta"].value = f"ETA: {int(eta_s)}s"

        self.main_page.update()

    def mark_done(self, transfer_id: str, path: str):
        if transfer_id in self.transfers_map:
            t = self.transfers_map[transfer_id]
            t["ring"].value = 1.0
            t["bar"].value = 1.0
            t["bar"].color = DSColor.SUCCESS
            t["txt_percent"].value = "100%"
            t["txt_percent"].color = DSColor.SUCCESS
            t["txt_speed"].value = "Hoàn tất"
            t["txt_speed"].color = DSColor.SUCCESS
            t["txt_eta"].value = "Đã xác thực SHA-256"
            self.main_page.update()
