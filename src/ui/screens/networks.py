from __future__ import annotations

from typing import Dict, List, Optional

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen
from kivy.factory import Factory

from ..components import Card
from ..theme import Theme


class NetworkRow(RecycleDataViewBehavior, BoxLayout):
    ssid = StringProperty("")
    bssid = StringProperty("")
    seen = StringProperty("-")
    rssi = StringProperty("-")
    theme_ref: Optional[Theme] = None

    def __init__(self, **kwargs) -> None:
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for NetworkRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.spacing = theme.gap_s
        self.label_ssid = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.38)
        self.label_bssid = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.34)
        self.label_rssi = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.14)
        self.label_seen = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.14)
        self.add_widget(self.label_ssid)
        self.add_widget(self.label_bssid)
        self.add_widget(self.label_rssi)
        self.add_widget(self.label_seen)

    def refresh_view_attrs(self, rv, index, data):
        self.ssid = data.get("ssid", "")
        self.bssid = data.get("bssid", "")
        self.rssi = str(data.get("rssi", "-"))
        self.seen = str(data.get("seen", "-"))
        self.label_ssid.text = self.ssid
        self.label_bssid.text = self.bssid
        self.label_rssi.text = self.rssi
        self.label_seen.text = self.seen
        return super().refresh_view_attrs(rv, index, data)


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

        self.status_card = Card(theme, orientation="vertical", padding=theme.gap_s, spacing=theme.gap_xs)
        self.status_label = Label(
            text="Monitoring stopped",
            color=theme.palette.text,
            font_size=theme.h3,
            size_hint_y=None,
            height=theme.dp(22),
            halign="left",
            valign="middle",
        )
        self.status_label.bind(size=lambda *_: setattr(self.status_label, "text_size", self.status_label.size))
        self.detail_label = Label(
            text="Start monitoring from the Dashboard to view nearby APs.",
            color=theme.palette.text_dim,
            font_size=theme.body,
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
        self.recycler = RecycleView()
        NetworkRow.theme_ref = theme
        Factory.register("NetworkRow", cls=NetworkRow)
        self.recycler.viewclass = "NetworkRow"
        layout = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout.default_size_hint = (1, None)
        layout.size_hint_y = None
        layout.bind(minimum_height=layout.setter("height"))
        self.recycler.add_widget(layout)
        self.recycler.layout_manager = layout
        list_card.add_widget(self.recycler)
        root.add_widget(list_card)

        self.add_widget(root)
        self.update_networks([])

    def update_networks(self, networks: List[Dict[str, object]]) -> None:
        self._networks = networks
        rows = []
        for item in networks:
            ssid = item.get("ssid") or "<hidden>"
            bssid = item.get("bssid") or "-"
            rssi = item.get("rssi")
            age = item.get("age_seconds")
            rows.append(
                {
                    "ssid": ssid,
                    "bssid": bssid,
                    "rssi": str(rssi) if rssi is not None else "-",
                    "seen": str(age) if age is not None else "0",
                }
            )
        placeholder = "No APs yet"
        self.recycler.data = rows or [{"ssid": placeholder, "bssid": "", "rssi": "", "seen": ""}]

    def update_status(
        self,
        status: Dict[str, object],
        running: bool,
        error: Optional[str],
    ) -> None:
        palette = self.theme.palette
        interface = status.get("interface") or getattr(self.app, "interface_choice", None) or "-"
        if error:
            self.status_card.background_color = list(palette.danger)
            self.status_label.text = "Monitoring unavailable"
            self.detail_label.text = str(error)
        elif running:
            self.status_card.background_color = list(palette.surface_alt)
            self.status_label.text = f"Listening on {interface}"
            if self._networks:
                self.detail_label.text = f"{len(self._networks)} access point(s) visible."
            else:
                self.detail_label.text = "Waiting for nearby AP beacons and probe responses..."
        else:
            self.status_card.background_color = list(palette.surface_alt)
            self.status_label.text = "Monitoring stopped"
            self.detail_label.text = "Start monitoring from the Dashboard to view nearby APs."
