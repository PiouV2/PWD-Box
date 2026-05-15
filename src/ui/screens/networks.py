from __future__ import annotations

from typing import Dict, List, Optional

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from ..components import Card
from ..theme import Theme


class NetworkRow(RecycleDataViewBehavior, BoxLayout):
    ssid = StringProperty("")
    bssid = StringProperty("")
    channel = StringProperty("-")
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
        self.label_channel = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.14)
        self.label_rssi = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.14)
        self.add_widget(self.label_ssid)
        self.add_widget(self.label_bssid)
        self.add_widget(self.label_channel)
        self.add_widget(self.label_rssi)

    def refresh_view_attrs(self, rv, index, data):
        self.ssid = data.get("ssid", "")
        self.bssid = data.get("bssid", "")
        self.channel = data.get("channel", "-")
        self.rssi = data.get("rssi", "-")
        self.label_ssid.text = self.ssid
        self.label_bssid.text = self.bssid
        self.label_channel.text = self.channel
        self.label_rssi.text = self.rssi
        return super().refresh_view_attrs(rv, index, data)


class NetworksScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="networks", **kwargs)
        self.app = app
        self.theme = theme
        self._networks: List[Dict[str, object]] = []
        self._filter_mode = self.app.network_filter_mode if self.app.network_filter_mode in {"weak", "strong", "all"} else "weak"

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_s,
        )

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.dp(28))
        header.add_widget(Label(text="Networks (Live)", color=theme.palette.text, font_size=theme.h2, size_hint_x=0.7))

        self.filter_button = Button(
            text=self._filter_mode.capitalize(),
            size_hint_x=0.3,
            background_normal="",
            background_color=theme.palette.surface_alt,
            color=theme.palette.text,
            font_size=theme.body,
        )
        self.filter_button.bind(on_press=self._cycle_filter)
        header.add_widget(self.filter_button)
        root.add_widget(header)

        table_header = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.row_height_compact)
        table_header.add_widget(Label(text="SSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.42))
        table_header.add_widget(Label(text="BSSID", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.3))
        table_header.add_widget(Label(text="CH", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.14))
        table_header.add_widget(Label(text="RSSI", color=theme.palette.text_dim, font_size=theme.caption, size_hint_x=0.14))
        root.add_widget(table_header)

        list_card = Card(theme, orientation="vertical", padding=[theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s])
        self.recycler = RecycleView()
        NetworkRow.theme_ref = theme
        self.recycler.viewclass = NetworkRow
        layout = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout.default_size_hint = (1, None)
        layout.size_hint_y = None
        layout.bind(minimum_height=layout.setter("height"))
        self.recycler.add_widget(layout)
        self.recycler.layout_manager = layout
        list_card.add_widget(self.recycler)
        root.add_widget(list_card)

        self.add_widget(root)

    def _cycle_filter(self, _instance) -> None:
        if self._filter_mode == "weak":
            self._filter_mode = "strong"
        elif self._filter_mode == "strong":
            self._filter_mode = "all"
        else:
            self._filter_mode = "weak"
        self.filter_button.text = self._filter_mode.capitalize()
        self.app.set_network_filter_mode(self._filter_mode)

    def update_networks(self, networks: List[Dict[str, object]]) -> None:
        self._networks = networks
        rows = []
        for item in networks:
            ssid = item.get("ssid") or "<hidden>"
            bssid = item.get("bssid") or "-"
            bssid_short = bssid if len(bssid) <= 12 else f"{bssid[:5]}..{bssid[-4:]}"
            channel = item.get("channel")
            rssi = item.get("rssi")
            rows.append(
                {
                    "ssid": ssid,
                    "bssid": bssid_short,
                    "channel": str(channel) if channel is not None else "-",
                    "rssi": str(rssi) if rssi is not None else "-",
                }
            )
        self.recycler.data = rows or [{"ssid": "No networks", "bssid": "", "channel": "", "rssi": ""}]
