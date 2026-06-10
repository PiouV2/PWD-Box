"""Reusable UI components for the Kivy app."""

from __future__ import annotations

from typing import Optional

from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from ..battery import BatterySnapshot, format_battery_status
from .theme import Theme


class Card(BoxLayout):
    """Surface container with a rounded background."""

    background_color = ListProperty([0.15, 0.16, 0.2, 1])
    radius = ListProperty([8, 8, 8, 8])

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a card with theme colors and rounded corners."""
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
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _sync_color(self, *_args) -> None:
        """Update the background color from the property."""
        self._color.rgba = self.background_color

    def _sync_radius(self, *_args) -> None:
        """Update the background corner radius."""
        self._rect.radius = self.radius


class PrimaryButton(Button):
    """Primary action button."""

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a primary button with theme styling."""
        super().__init__(**kwargs)
        self.theme = theme
        self.size_hint_y = None
        self.height = theme.button_height
        self.background_normal = ""
        self.background_color = theme.palette.accent
        self.color = theme.palette.text
        self.font_size = theme.h3


class SecondaryButton(Button):
    """Secondary action button."""

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a secondary button with theme styling."""
        super().__init__(**kwargs)
        self.theme = theme
        self.size_hint_y = None
        self.height = theme.button_height
        self.background_normal = ""
        self.background_color = theme.palette.surface_alt
        self.color = theme.palette.text
        self.font_size = theme.h3


class BigNavButton(ButtonBehavior, BoxLayout):
    """Compact navigation row for the Settings hub."""

    title = StringProperty("")
    subtitle = StringProperty("")

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a two-line navigation button."""
        super().__init__(orientation="vertical", size_hint_y=None, height=theme.dp(76), **kwargs)
        self.theme = theme
        self.padding = [theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s]
        self.spacing = theme.gap_xs
        self.background_color = list(theme.palette.surface_alt)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[theme.radius] * 4)
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self.title_label = Label(
            text=self.title,
            color=theme.palette.text,
            font_size=theme.h3,
            halign="left",
            size_hint_y=None,
            height=theme.dp(24),
        )
        self.subtitle_label = Label(
            text=self.subtitle,
            color=theme.palette.text_dim,
            font_size=theme.caption,
            halign="left",
            size_hint_y=None,
            height=theme.dp(18),
        )
        self.title_label.bind(size=lambda *_: setattr(self.title_label, "text_size", self.title_label.size))
        self.subtitle_label.bind(size=lambda *_: setattr(self.subtitle_label, "text_size", self.subtitle_label.size))
        self.add_widget(self.title_label)
        self.add_widget(self.subtitle_label)
        self.bind(title=self._update_title)
        self.bind(subtitle=self._update_subtitle)

    def _sync_rect(self, *_args) -> None:
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_title(self, *_args) -> None:
        """Refresh the title text."""
        self.title_label.text = self.title

    def _update_subtitle(self, *_args) -> None:
        """Refresh the subtitle text."""
        self.subtitle_label.text = self.subtitle


class StatusChip(BoxLayout):
    """Small status badge with tone colors."""

    text = StringProperty("")
    tone = StringProperty("neutral")

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a status chip with label and background."""
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
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_text(self, *_args) -> None:
        """Refresh the label text."""
        self.label.text = self.text

    def _update_tone(self, *_args) -> None:
        """Update the background color for the tone."""
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


class BatteryStatusChip(BoxLayout):
    """Compact battery status chip."""

    text = StringProperty("")
    tone = StringProperty("neutral")

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a battery chip with truncation support."""
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.dp(24), **kwargs)
        self.theme = theme
        self.background_color = list(theme.palette.surface_alt)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[theme.radius_small] * 4)
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self.label = Label(
            text=self.text,
            color=theme.palette.text,
            font_size=theme.caption,
            halign="right",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self.label.bind(size=lambda *_: setattr(self.label, "text_size", self.label.size))
        self.add_widget(self.label)
        self.bind(text=self._update_text)
        self.bind(tone=self._update_tone)

    def _sync_rect(self, *_args) -> None:
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_text(self, *_args) -> None:
        """Refresh the label text."""
        self.label.text = self.text

    def _update_tone(self, *_args) -> None:
        """Update the background color for the tone."""
        palette = self.theme.palette
        if self.tone == "ok":
            color = palette.accent_alt
        elif self.tone == "warn":
            color = palette.warning
        else:
            color = palette.surface_alt
        self._color.rgba = color

    def set_snapshot(self, snapshot: BatterySnapshot) -> None:
        """Update the chip from a battery snapshot."""
        self.text = format_battery_status(snapshot)
        self.tone = snapshot.tone


class AlertBanner(Card):
    """Banner used to highlight warnings or alerts."""

    def __init__(self, theme: Theme, **kwargs) -> None:
        """Create a hidden banner that can be shown later."""
        super().__init__(theme, **kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 0
        self.padding = [theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s]
        self.spacing = theme.gap_s
        self.message_label = Label(text="", color=theme.palette.text, font_size=theme.body)
        self.add_widget(self.message_label)

    def show(self, message: str, tone: str = "warn") -> None:
        """Show the banner with a message and tone."""
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
        """Hide the banner and clear its text."""
        self.message_label.text = ""
        self.height = 0
        self.opacity = 0


class HeaderBar(BoxLayout):
    """Top bar with title, status, and battery info."""

    def __init__(self, theme: Theme, title: str, **kwargs) -> None:
        """Create the header bar widgets."""
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.header_height, **kwargs)
        self.theme = theme
        self.padding = [theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s]
        self.spacing = theme.gap_m
        self.background_color = list(theme.palette.surface)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self.title_label = Label(text=title, color=theme.palette.text, font_size=theme.h2, size_hint_x=0.3, halign="left")
        self.title_label.bind(size=lambda *_: setattr(self.title_label, "text_size", self.title_label.size))
        self.spacer = Widget(size_hint_x=0.2)
        self.message_label = Label(
            text="",
            color=theme.palette.warning,
            font_size=theme.caption,
            size_hint_x=0.12,
            halign="right",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        self.message_label.bind(size=lambda *_: setattr(self.message_label, "text_size", self.message_label.size))
        self.status_chip = StatusChip(theme)
        self.status_chip.size_hint_x = 0.12
        self.status_chip.text = "STOPPED"
        self.status_chip.tone = "neutral"
        self.battery_chip = BatteryStatusChip(theme)
        self.battery_chip.size_hint_x = 0.26
        self.battery_chip.set_snapshot(BatterySnapshot.unavailable())

        self.add_widget(self.title_label)
        self.add_widget(self.spacer)
        self.add_widget(self.status_chip)
        self.add_widget(self.message_label)
        self.add_widget(self.battery_chip)

    def _sync_rect(self, *_args) -> None:
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def update_status(self, text: str, tone: str) -> None:
        """Update the status chip text and tone."""
        self.status_chip.text = text
        self.status_chip.tone = tone

    def update_battery(self, snapshot: BatterySnapshot) -> None:
        """Update the battery chip from a snapshot."""
        self.battery_chip.set_snapshot(snapshot)

    def set_message(self, message: Optional[str], tone: str = "warn") -> None:
        """Update the message text and color."""
        palette = self.theme.palette
        if tone == "error":
            color = palette.danger
        elif tone == "ok":
            color = palette.success
        elif tone == "neutral":
            color = palette.text_dim
        else:
            color = palette.warning
        self.message_label.color = color
        self.message_label.text = message or ""


class FooterNav(BoxLayout):
    """Bottom navigation bar for primary screens."""

    def __init__(self, theme: Theme, app, **kwargs) -> None:
        """Create navigation buttons bound to screen names."""
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.nav_height, **kwargs)
        self.theme = theme
        self.padding = [theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s]
        self.spacing = theme.gap_s
        self.background_color = list(theme.palette.surface)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, 0, 0])
        self.bind(pos=self._sync_rect, size=self._sync_rect)

        self._app = app
        self._buttons = {}
        for name, label in (
            ("dashboard", "Dashboard"),
            ("networks", "Networks"),
            ("alerts", "Alerts"),
            ("settings", "Settings"),
        ):
            button = SecondaryButton(theme, text=label)
            button.size_hint_y = 1
            button.bind(on_press=self._make_handler(name))
            self._buttons[name] = button
            self.add_widget(button)

    def _sync_rect(self, *_args) -> None:
        """Keep the background rectangle aligned with layout."""
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _make_handler(self, name: str):
        """Return a click handler that switches screens via the app."""
        def _handler(_instance):
            self._app.show_screen(name)

        return _handler
