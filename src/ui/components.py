from __future__ import annotations

from typing import Optional

from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from .theme import Theme


class Card(BoxLayout):
    background_color = ListProperty([0.15, 0.16, 0.2, 1])
    radius = ListProperty([8, 8, 8, 8])

    def __init__(self, theme: Theme, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.background_color = list(theme.palette.surface)
        self.radius = [theme.radius] * 4
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
        self.bind(pos=self._sync_rect, size=self._sync_rect)
        self.bind(background_color=self._sync_color, radius=self._sync_radius)

    def _sync_rect(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _sync_color(self, *_args) -> None:
        self._color.rgba = self.background_color

    def _sync_radius(self, *_args) -> None:
        self._rect.radius = self.radius


class PrimaryButton(Button):
    def __init__(self, theme: Theme, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.size_hint_y = None
        self.height = theme.button_height
        self.background_normal = ""
        self.background_color = theme.palette.accent
        self.color = theme.palette.text
        self.font_size = theme.h3


class SecondaryButton(Button):
    def __init__(self, theme: Theme, **kwargs) -> None:
        super().__init__(**kwargs)
        self.theme = theme
        self.size_hint_y = None
        self.height = theme.button_height
        self.background_normal = ""
        self.background_color = theme.palette.surface_alt
        self.color = theme.palette.text
        self.font_size = theme.h3


class StatusChip(BoxLayout):
    text = StringProperty("")
    tone = StringProperty("neutral")

    def __init__(self, theme: Theme, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.dp(24), **kwargs)
        self.theme = theme
        self.background_color = list(theme.palette.surface_alt)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[theme.radius_small] * 4)
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self.label = Label(text=self.text, color=theme.palette.text, font_size=theme.body)
        self.add_widget(self.label)
        self.bind(text=self._update_text)
        self.bind(tone=self._update_tone)

    def _sync_rect(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_text(self, *_args) -> None:
        self.label.text = self.text

    def _update_tone(self, *_args) -> None:
        palette = self.theme.palette
        if self.tone == "ok":
            color = palette.success
        elif self.tone == "warn":
            color = palette.warning
        elif self.tone == "error":
            color = palette.danger
        else:
            color = palette.surface_alt
        self._color.rgba = color


class AlertBanner(Card):
    def __init__(self, theme: Theme, **kwargs) -> None:
        super().__init__(theme, **kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 0
        self.padding = [theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s]
        self.spacing = theme.gap_s
        self.message_label = Label(text="", color=theme.palette.text, font_size=theme.body)
        self.add_widget(self.message_label)

    def show(self, message: str, tone: str = "warn") -> None:
        palette = self.theme.palette
        if tone == "error":
            self.background_color = list(palette.danger)
        elif tone == "ok":
            self.background_color = list(palette.success)
        else:
            self.background_color = list(palette.warning)
        self.message_label.text = message
        self.height = self.theme.banner_height
        self.opacity = 1

    def hide(self) -> None:
        self.message_label.text = ""
        self.height = 0
        self.opacity = 0


class HeaderBar(BoxLayout):
    def __init__(self, theme: Theme, title: str, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.header_height, **kwargs)
        self.theme = theme
        self.padding = [theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s]
        self.spacing = theme.gap_m
        self.background_color = list(theme.palette.surface)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self.title_label = Label(text=title, color=theme.palette.text, font_size=theme.h2, size_hint_x=0.45, halign="left")
        self.title_label.bind(size=lambda *_: setattr(self.title_label, "text_size", self.title_label.size))
        self.status_chip = StatusChip(theme)
        self.status_chip.text = "STOPPED"
        self.status_chip.tone = "neutral"
        self.message_label = Label(text="", color=theme.palette.warning, font_size=theme.caption, halign="right")
        self.message_label.bind(size=lambda *_: setattr(self.message_label, "text_size", self.message_label.size))

        self.add_widget(self.title_label)
        self.add_widget(self.status_chip)
        self.add_widget(self.message_label)

    def _sync_rect(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def update_status(self, text: str, tone: str) -> None:
        self.status_chip.text = text
        self.status_chip.tone = tone

    def set_message(self, message: Optional[str]) -> None:
        self.message_label.text = message or ""


class FooterNav(BoxLayout):
    def __init__(self, theme: Theme, screen_manager, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.nav_height, **kwargs)
        self.theme = theme
        self.padding = [theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s]
        self.spacing = theme.gap_s
        self.background_color = list(theme.palette.surface)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self._screen_manager = screen_manager
        self._buttons = {}
        for name, label in (
            ("dashboard", "Dashboard"),
            ("networks", "Networks"),
            ("alerts", "Alerts"),
            ("history", "History"),
            ("settings", "Settings"),
            ("diagnostics", "Health"),
        ):
            button = SecondaryButton(theme, text=label)
            button.size_hint_y = 1
            button.bind(on_press=self._make_handler(name))
            self._buttons[name] = button
            self.add_widget(button)

    def _sync_rect(self, *_args) -> None:
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _make_handler(self, name: str):
        def _handler(_instance):
            self._screen_manager.current = name

        return _handler
