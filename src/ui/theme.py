from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from kivy.core.window import Window
from kivy.metrics import dp, sp


Color = Tuple[float, float, float, float]


@dataclass(frozen=True)
class Palette:
    background: Color
    surface: Color
    surface_alt: Color
    text: Color
    text_dim: Color
    accent: Color
    accent_alt: Color
    success: Color
    warning: Color
    danger: Color
    divider: Color


DARK_PALETTE = Palette(
    background=(0.07, 0.08, 0.1, 1),
    surface=(0.12, 0.13, 0.16, 1),
    surface_alt=(0.16, 0.17, 0.2, 1),
    text=(0.96, 0.97, 0.99, 1),
    text_dim=(0.72, 0.75, 0.8, 1),
    accent=(0.2, 0.62, 0.7, 1),
    accent_alt=(0.36, 0.78, 0.52, 1),
    success=(0.3, 0.8, 0.5, 1),
    warning=(0.95, 0.66, 0.22, 1),
    danger=(0.92, 0.28, 0.3, 1),
    divider=(0.22, 0.24, 0.28, 1),
)

LIGHT_PALETTE = Palette(
    background=(0.93, 0.94, 0.96, 1),
    surface=(0.98, 0.98, 0.99, 1),
    surface_alt=(0.9, 0.92, 0.95, 1),
    text=(0.12, 0.14, 0.18, 1),
    text_dim=(0.35, 0.38, 0.42, 1),
    accent=(0.12, 0.5, 0.66, 1),
    accent_alt=(0.16, 0.62, 0.36, 1),
    success=(0.2, 0.65, 0.35, 1),
    warning=(0.76, 0.46, 0.12, 1),
    danger=(0.8, 0.2, 0.22, 1),
    divider=(0.75, 0.78, 0.82, 1),
)


class Theme:
    def __init__(self, mode: str = "dark") -> None:
        self.mode = mode
        self.palette = DARK_PALETTE if mode == "dark" else LIGHT_PALETTE
        self.scale = self._calculate_scale()

        self.h1 = self.sp(20)
        self.h2 = self.sp(18)
        self.h3 = self.sp(16)
        self.body = self.sp(14)
        self.caption = self.sp(12)

        self.radius = self.dp(10)
        self.radius_small = self.dp(6)
        self.gap_xs = self.dp(4)
        self.gap_s = self.dp(6)
        self.gap_m = self.dp(10)
        self.gap_l = self.dp(14)

        self.row_height = self.dp(26)
        self.row_height_compact = self.dp(22)
        self.button_height = self.dp(44)
        self.nav_height = self.dp(44)
        self.header_height = self.dp(50)
        self.banner_height = self.dp(32)

    def _calculate_scale(self) -> float:
        width = max(Window.width, 1)
        height = max(Window.height, 1)
        return min(width / 800.0, height / 480.0)

    def dp(self, value: float) -> float:
        return dp(value * self.scale)

    def sp(self, value: float) -> float:
        return sp(value * self.scale)


def resolve_theme(mode: str) -> Theme:
    return Theme(mode=mode)
