"""Diagnostics screen for device checks."""

from __future__ import annotations

import threading

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from ..components import PrimaryButton
from ..theme import Theme
from ...health import format_results, run_health_check


class DiagnosticsScreen(Screen):
    """Screen that runs and displays health checks."""

    def __init__(self, app, theme: Theme, **kwargs) -> None:
        """Build the diagnostics layout."""
        super().__init__(name="diagnostics", **kwargs)
        self.app = app
        self.theme = theme
        self._busy = False

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_s,
        )

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.dp(28))
        header.add_widget(Label(text="Device checks", color=theme.palette.text, font_size=theme.h2, size_hint_x=0.7))
        self.run_button = PrimaryButton(theme, text="Run device checks")
        self.run_button.bind(on_press=lambda *_: self.run_checks())
        header.add_widget(self.run_button)
        root.add_widget(header)

        self.output = TextInput(
            text="Run device checks to view status",
            readonly=True,
            background_color=theme.palette.surface_alt,
            foreground_color=theme.palette.text,
            font_size=theme.body,
        )
        root.add_widget(self.output)

        self.add_widget(root)

    def run_checks(self) -> None:
        """Start health checks in a background thread."""
        if self._busy:
            return
        self._busy = True
        self.run_button.text = "Running..."
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        """Run health checks and schedule UI update."""
        results = run_health_check(self.app.app_config, interface=self.app.interface_choice)
        text = format_results(results)
        Clock.schedule_once(lambda *_: self._update(text), 0)

    def _update(self, text: str) -> None:
        """Update the output text and reset the UI."""
        self.output.text = text
        self.run_button.text = "Run device checks"
        self._busy = False
