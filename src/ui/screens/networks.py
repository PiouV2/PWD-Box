from __future__ import annotations

from typing import Dict, List, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from ..components import Card
from ..theme import Theme


class NetworkRow(BoxLayout):
    def __init__(self, theme: Theme, ssid: str, bssid: str, rssi: str, seen: str, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, spacing=theme.gap_s, **kwargs)
        self.add_widget(Label(text=ssid, color=theme.palette.text, font_size=theme.body, size_hint_x=0.38))
        self.add_widget(Label(text=bssid, color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.34))
        self.add_widget(Label(text=rssi, color=theme.palette.text, font_size=theme.body, size_hint_x=0.14))
        self.add_widget(Label(text=seen, color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.14))


class NetworksScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="networks", **kwargs)
        self.app = app
        self.theme = theme
        self._networks: List[Dict[str, object]] = []

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_s,
        )

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.dp(28))
        header.add_widget(Label(text="Networks (Live)", color=theme.palette.text, font_size=theme.h2, size_hint_x=0.7))
        root.add_widget(header)

        self.status_card = Card(theme, orientation="vertical", padding=theme.gap_s, spacing=theme.gap_xs, size_hint_y=None)
        self.status_card.height = 0
        self.status_card.opacity = 0
        self.status_label = Label(
            text="",
            color=theme.palette.text,
            font_size=theme.body,
            size_hint_y=None,
            height=theme.dp(22),
            halign="left",
            valign="middle",
        )
        self.status_label.bind(size=lambda *_: setattr(self.status_label, "text_size", self.status_label.size))
        self.detail_label = Label(
            text="",
            color=theme.palette.text_dim,
            font_size=theme.caption,
            size_hint_y=None,
            height=theme.dp(42),
            halign="left",
            valign="middle",
        )
        self.detail_label.bind(size=lambda *_: setattr(self.detail_label, "text_size", self.detail_label.size))
        self.status_card.add_widget(self.status_label)
        self.status_card.add_widget(self.detail_label)
        root.add_widget(self.status_card)

        table_header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.row_height_compact)
        table_header.add_widget(Label(text="SSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.38))
        table_header.add_widget(Label(text="BSSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.34))
        table_header.add_widget(Label(text="RSSI", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.14))
        table_header.add_widget(Label(text="Seen(s)", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.14))
        root.add_widget(table_header)

        list_card = Card(theme, orientation="vertical", padding=[theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s])
        self.rows_scroll = ScrollView(do_scroll_x=False)
        self.rows_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=theme.gap_xs)
        self.rows_container.bind(minimum_height=self.rows_container.setter("height"))
        self.rows_scroll.add_widget(self.rows_container)
        list_card.add_widget(self.rows_scroll)
        root.add_widget(list_card)

        self.add_widget(root)
        self.update_networks([])

    def update_networks(self, networks: List[Dict[str, object]]) -> None:
        self._networks = networks
        self.rows_container.clear_widgets()
        for item in networks:
            ssid = item.get("ssid") or "<hidden>"
            bssid = item.get("bssid") or "-"
            rssi = item.get("rssi")
            age = item.get("age_seconds")
            row = NetworkRow(
                self.theme,
                ssid=str(ssid),
                bssid=str(bssid),
                rssi=str(rssi) if rssi is not None else "-",
                seen=str(age) if age is not None else "0",
            )
            self.rows_container.add_widget(row)
        placeholder = "No APs yet"
        if not networks:
            self.rows_container.add_widget(
                NetworkRow(self.theme, ssid=placeholder, bssid="", rssi="", seen="")
            )

    def update_status(
        self,
        status: Dict[str, object],
        running: bool,
        error: Optional[str],
    ) -> None:
        palette = self.theme.palette
        if error:
            self.status_card.height = self.theme.dp(72)
            self.status_card.opacity = 1
            self.status_card.background_color = list(palette.danger)
            self.status_label.text = "Monitoring unavailable"
            self.detail_label.text = str(error)
        else:
            self.status_card.height = 0
            self.status_card.opacity = 0
            self.status_card.background_color = list(palette.surface_alt)
            self.status_label.text = ""
            self.detail_label.text = ""
