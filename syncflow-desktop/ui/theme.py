import flet as ft

class DSColor:
    PRIMARY = "#E2725B"       # Terra Cotta
    BACKGROUND = "#16181D"    # Deep dark (Forbidden #000)
    SURFACE = "#1C1E24"
    SURFACE_HIGH = "#24272E"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_MUTED = "#8E8E93"
    SUCCESS = "#58BA89"
    WARNING = "#F0B45A"
    BORDER = "#333742"

class DSSpacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
    XXXL = 32

class DSRadius:
    BUTTON = 10
    INPUT = 12
    CARD = 16
    ICON_BLOCK = 8

def get_app_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=DSColor.PRIMARY,
        visual_density=ft.VisualDensity.COMFORTABLE,
        font_family="sans-serif",
    )
