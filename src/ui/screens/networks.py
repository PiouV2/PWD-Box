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
        self.label_ssid = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.42)
        self.label_bssid = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.3)
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

        table_header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.row_height_compact)
        table_header.add_widget(Label(text="SSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.42))
        table_header.add_widget(Label(text="BSSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.3))
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

    def update_networks(self, networks: List[Dict[str, object]]) -> None:
        self._networks = networks
        rows = []
        for item in networks:
            ssid = item.get("ssid") or "<hidden>"
            bssid = item.get("bssid") or "-"
            bssid_short = bssid if len(bssid) <= 12 else f"{bssid[:5]}..{bssid[-4:]}"
            rssi = item.get("rssi")
            age = item.get("age_seconds")
            rows.append(
                {
                    "ssid": ssid,
                    "bssid": bssid_short,
                    "rssi": str(rssi) if rssi is not None else "-",
                    "seen": str(age) if age is not None else "0",
                }
            )
        placeholder = "No networks"
        self.recycler.data = rows or [{"ssid": placeholder, "bssid": "", "rssi": "", "seen": ""}]
