from __future__ import annotations

import threading
from typing import List

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from ..components import Card, PrimaryButton
from ..theme import Theme
from ...health import format_results, run_health_check


class ResultRow(RecycleDataViewBehavior, BoxLayout):
    theme_ref: Theme = None

    def __init__(self, **kwargs) -> None:
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for ResultRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.label = Label(color=theme.palette.text, font_size=theme.body)
        self.add_widget(self.label)

    def refresh_view_attrs(self, rv, index, data):
        self.label.text = data.get("text", "")
        return super().refresh_view_attrs(rv, index, data)


class DiagnosticsScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
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

        hint = Label(
            text="Checks permissions, Wi-Fi adapter, packages, and battery status.",
            color=theme.palette.text_dim,
            font_size=theme.caption,
            size_hint_y=None,
            height=theme.dp(18),
        )
        root.add_widget(hint)

        list_card = Card(theme, orientation="vertical", padding=theme.gap_s, spacing=theme.gap_s)
        self.results_view = RecycleView()
        ResultRow.theme_ref = theme
        self.results_view.viewclass = ResultRow
        layout = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout.default_size_hint = (1, None)
        layout.size_hint_y = None
        layout.bind(minimum_height=layout.setter("height"))
        self.results_view.add_widget(layout)
        self.results_view.layout_manager = layout
        list_card.add_widget(self.results_view)
        root.add_widget(list_card)
        self.results_view.data = [{"text": "Run device checks to view status"}]

        self.details = TextInput(
            text="",
            readonly=True,
            size_hint_y=None,
            height=theme.dp(120),
            background_color=theme.palette.surface_alt,
            foreground_color=theme.palette.text,
        )
        root.add_widget(self.details)

        self.add_widget(root)

    def run_checks(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.run_button.text = "Running..."
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self) -> None:
        results = run_health_check(self.app.app_config, interface=self.app.interface_choice)
        lines = [f"[{ 'PASS' if r.ok else 'FAIL' }] {r.name}: {r.details}" for r in results]
        details = format_results(results)
        Clock.schedule_once(lambda *_: self._update(lines, details), 0)

    def _update(self, lines: List[str], details: str) -> None:
        self.results_view.data = [{"text": line} for line in lines]
        self.details.text = details
        self.run_button.text = "Run device checks"
        self._busy = False
