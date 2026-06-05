"""Small reusable widgets for the UI."""

from __future__ import annotations

from typing import Callable

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from .components import SecondaryButton
from .theme import Theme


class Stepper(BoxLayout):
    """Numeric stepper with plus/minus buttons."""

    def __init__(self, theme: Theme, label: str, value: int, step: int, on_change: Callable[[int], None], **kwargs) -> None:
        """Create a stepper row with callbacks."""
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s, **kwargs)
        self.theme = theme
        self.value = value
        self.step = step
        self.on_change = on_change

        self.label = Label(text=label, color=theme.palette.text, font_size=theme.body, size_hint_x=0.5)
        self.value_label = Label(text=str(value), color=theme.palette.text, font_size=theme.body, size_hint_x=0.2)
        self.minus = SecondaryButton(theme, text="-")
        self.plus = SecondaryButton(theme, text="+")
        self.minus.bind(on_press=lambda *_: self._update(-self.step))
        self.plus.bind(on_press=lambda *_: self._update(self.step))
        self.add_widget(self.label)
        self.add_widget(self.minus)
        self.add_widget(self.value_label)
        self.add_widget(self.plus)

    def _update(self, delta: int) -> None:
        """Apply the delta and notify the handler."""
        self.value = max(0, self.value + delta)
        self.value_label.text = str(self.value)
        self.on_change(self.value)
