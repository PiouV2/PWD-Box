from __future__ import annotations

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from ..components import BigNavButton, Card, SecondaryButton
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

        header_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.nav_height, spacing=theme.gap_s)
        back = SecondaryButton(theme, text="Back")
        back.size_hint_x = 0.22
        back.bind(on_press=lambda *_: self.app.show_screen("dashboard"))
        title = Label(text="Settings", color=theme.palette.text, font_size=theme.h2, halign="left")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        header_row.add_widget(back)
        header_row.add_widget(title)
        root.add_widget(header_row)

        center = AnchorLayout(anchor_x="center", anchor_y="center")
        hub_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint=(None, None),
            width=theme.dp(620),
        )
        hub_card.bind(minimum_height=hub_card.setter("height"))

        # Settings hub: three compact, touch-friendly navigation buttons.
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

        hub_card.add_widget(self.network_button)
        hub_card.add_widget(self.evidence_button)
        hub_card.add_widget(self.system_button)
        center.add_widget(hub_card)
        root.add_widget(center)

        hint = Label(
            text="Tap a category to configure settings.",
            color=theme.palette.text_dim,
            font_size=theme.caption,
            size_hint_y=None,
            height=theme.dp(18),
        )
        root.add_widget(hint)

        self.add_widget(root)

    def refresh(self) -> None:
        return None
