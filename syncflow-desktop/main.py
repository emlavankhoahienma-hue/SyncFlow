import asyncio
import threading
import socket
import logging
import sys
from pathlib import Path
import flet as ft
import uvicorn

from server.api import app as fastapi_app
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
            padding=ft.padding.symmetric(vertical=DSSpacing.LG),
            content=ft.Container(
                width=36,
                height=36,
                border_radius=DSRadius.ICON_BLOCK,
                bgcolor=DSColor.PRIMARY,
                alignment=ft.alignment.center,
                content=ft.Icon(ft.icons.SYNC_ROUNDED, color=ft.colors.WHITE, size=20),
            )
        ),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME_ROUNDED,
                label="Trang chủ"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.UPLOAD_OUTLINED,
                selected_icon=ft.icons.UPLOAD_ROUNDED,
                label="Gửi"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.icons.DOWNLOAD_ROUNDED,
                label="Nhận"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.TIMELAPSE_OUTLINED,
                selected_icon=ft.icons.TIMELAPSE_ROUNDED,
                label="Tiến độ"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS_ROUNDED,
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
