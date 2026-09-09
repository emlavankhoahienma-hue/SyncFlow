import asyncio
import threading
import socket
import logging
import sys
from pathlib import Path
import flet as ft
import uvicorn

from server.api import app as fastapi_app
from server.ws import ws_manager
from server.discovery import BonjourServer
from ui.theme import DSColor, DSSpacing, DSRadius, get_app_theme
from ui.home_page import HomePage
from ui.send_page import SendPage
from ui.receive_page import ReceivePage
from ui.progress_page import ProgressPage
from ui.settings_page import SettingsPage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("syncflow.desktop")

# Server thread runner
def run_fastapi_server():
    config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=8765,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.run()

def main(page: ft.Page):
    page.title = "SyncFlow Desktop"
    if hasattr(page, "window") and page.window is not None:
        try:
            page.window.width = 1000
            page.window.height = 700
            page.window.min_width = 800
            page.window.min_height = 600
        except Exception:
            pass
    page.bgcolor = DSColor.BACKGROUND
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = get_app_theme()
    page.padding = 0

    # Initialize Pages
    progress_page = ProgressPage(page)
    
    def on_nav_change(index: int):
        rail.selected_index = index
        render_content(index)

    home_page = HomePage(page, on_navigate=on_nav_change)
    send_page = SendPage(page)
    receive_page = ReceivePage(page)
    settings_page = SettingsPage(page)

    pages = [home_page, send_page, receive_page, progress_page, settings_page]

    # WebSocket Realtime Event Listener
    def on_ws_event(event: dict):
        event_type = event.get("type")
        if event_type == "progress":
            transfer_id = event.get("transfer_id", "")
            sent = event.get("sent", 0)
            total = event.get("total", 0)
            speed = event.get("speed_bps", 0.0)
            eta = event.get("eta_s", 0.0)

            def _update():
                progress_page.update_progress(transfer_id, sent, total, speed, eta)
                percent = (sent / total) if total > 0 else 0.0
                home_page.update_transfer(
                    f"Tác vụ #{transfer_id[:6]}",
                    percent,
                    sent / (1024 * 1024),
                    total / (1024 * 1024),
                    speed / (1024 * 1024),
                    eta
                )

            try:
                if hasattr(page, "run_thread"):
                    page.run_thread(_update)
                else:
                    _update()
            except Exception:
                pass

        elif event_type == "done":
            transfer_id = event.get("transfer_id", "")
            path = event.get("path", "")

            def _done():
                progress_page.mark_done(transfer_id, path)
                home_page.mark_completed(Path(path).name if path else "Tệp")
                receive_page.content = receive_page.build_ui()
                page.update()

            try:
                if hasattr(page, "run_thread"):
                    page.run_thread(_done)
                else:
                    _done()
            except Exception:
                pass

    ws_manager.add_listener(on_ws_event)

    content_area = ft.Container(
        expand=True,
        content=home_page,
    )

    def render_content(index: int):
        content_area.content = pages[index]
        page.update()

    def on_rail_selected(e):
        render_content(e.control.selected_index)

    # Navigation Rail (Left side)
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        min_extended_width=160,
        bgcolor=DSColor.SURFACE,
        indicator_color=DSColor.PRIMARY,
        leading=ft.Container(
            padding=ft.Padding.symmetric(vertical=DSSpacing.LG),
            content=ft.Container(
                width=36,
                height=36,
                border_radius=DSRadius.ICON_BLOCK,
                bgcolor=DSColor.PRIMARY,
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.SYNC_ROUNDED, color=ft.Colors.WHITE, size=20),
            )
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.HOME_OUTLINED,
                selected_icon=ft.Icons.HOME_ROUNDED,
                label="Trang chủ"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.UPLOAD_OUTLINED,
                selected_icon=ft.Icons.UPLOAD_ROUNDED,
                label="Gửi"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.Icons.DOWNLOAD_ROUNDED,
                label="Nhận"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.TIMELAPSE_OUTLINED,
                selected_icon=ft.Icons.TIMELAPSE_ROUNDED,
                label="Tiến độ"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS_ROUNDED,
                label="Cài đặt"
            ),
        ],
        on_change=on_rail_selected,
    )

    layout = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            rail,
            ft.VerticalDivider(width=1, color=DSColor.BORDER),
            content_area,
        ]
    )

    page.add(layout)

if __name__ == "__main__":
    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=run_fastapi_server, daemon=True)
    server_thread.start()
    logger.info("FastAPI server started on port 8765")

    # Start Bonjour service
    bonjour = BonjourServer(port=8765)
    bonjour.start()

    try:
        ft.app(target=main)
    finally:
        bonjour.stop()
