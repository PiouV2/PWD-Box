from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from ..components import BigNavButton
from ..theme import Theme


class SettingsScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="settings", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )

        header = Label(text="Settings", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(28))
        root.add_widget(header)

        # Settings hub: three large, touch-friendly navigation buttons.
        self.network_button = BigNavButton(
            theme,
            title="Network",
            subtitle="Interface selection, monitor mode",
        )
        self.evidence_button = BigNavButton(
            theme,
            title="Evidence (PCAP)",
            subtitle="Capture on alert, retention, path",
        )
        self.system_button = BigNavButton(
            theme,
            title="System",
            subtitle="Theme, diagnostics, storage",
        )
        self.network_button.bind(on_press=lambda *_: self.app.show_screen("settings_network"))
        self.evidence_button.bind(on_press=lambda *_: self.app.show_screen("settings_evidence"))
        self.system_button.bind(on_press=lambda *_: self.app.show_screen("settings_system"))

        root.add_widget(self.network_button)
        root.add_widget(self.evidence_button)
        root.add_widget(self.system_button)

        self.add_widget(root)

    def refresh(self) -> None:
        return None
