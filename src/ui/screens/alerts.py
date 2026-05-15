from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from ..components import Card
from ..theme import Theme


class AlertRow(RecycleDataViewBehavior, BoxLayout):
    timestamp = StringProperty("")
    alert_type = StringProperty("")
    summary = StringProperty("")
    pcap = StringProperty("")

    theme_ref: Theme = None

    def __init__(self, **kwargs) -> None:
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for AlertRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.spacing = theme.gap_s
        self.alert_data: Dict[str, object] = {}

        self.label_ts = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.28)
        self.label_type = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.2)
        self.label_summary = Label(color=theme.palette.text, font_size=theme.body, size_hint_x=0.42)
        self.label_pcap = Label(color=theme.palette.text_dim, font_size=theme.body, size_hint_x=0.1)
        self.add_widget(self.label_ts)
        self.add_widget(self.label_type)
        self.add_widget(self.label_summary)
        self.add_widget(self.label_pcap)

    def refresh_view_attrs(self, rv, index, data):
        self.alert_data = data.get("alert_data", {})
        self.timestamp = data.get("timestamp", "")
        self.alert_type = data.get("alert_type", "")
        self.summary = data.get("summary", "")
        self.pcap = data.get("pcap", "")
        self.label_ts.text = self.timestamp
        self.label_type.text = self.alert_type
        self.label_summary.text = self.summary
        self.label_pcap.text = self.pcap
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._show_details()
        return True

    def _show_details(self) -> None:
        details = self.alert_data
        message = [
            f"Time: {details.get('timestamp')}",
            f"Type: {details.get('alert_type')}",
            f"Key: {details.get('key')}",
            f"Count: {details.get('count')}",
        ]
        if details.get("pcap_path"):
            message.append(f"PCAP: {details.get('pcap_path')}")
        content = Label(text="\n".join(message), color=self.theme.palette.text)
        popup = Popup(title="Alert Details", content=content, size_hint=(0.8, 0.6))
        popup.open()


class AlertsScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="alerts", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_s,
        )

        header = Label(text="Alerts (Live)", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(28))
        root.add_widget(header)

        list_card = Card(theme, orientation="vertical", padding=[theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s])
        self.recycler = RecycleView()
        AlertRow.theme_ref = theme
        self.recycler.viewclass = AlertRow
        layout = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout.default_size_hint = (1, None)
        layout.size_hint_y = None
        layout.bind(minimum_height=layout.setter("height"))
        self.recycler.layout_manager = layout
        list_card.add_widget(self.recycler)
        root.add_widget(list_card)

        self.add_widget(root)

    def update_alerts(self, alerts: List[Dict[str, object]]) -> None:
        rows = []
        for alert in alerts:
            key = alert.get("key") or "-"
            summary = key if len(key) <= 20 else f"{key[:8]}..{key[-6:]}"
            pcap_path = alert.get("pcap_path")
            pcap = Path(pcap_path).name if pcap_path else "-"
            rows.append(
                {
                    "timestamp": alert.get("timestamp", ""),
                    "alert_type": alert.get("alert_type", ""),
                    "summary": summary,
                    "pcap": pcap,
                    "alert_data": alert,
                }
            )
        self.recycler.data = rows or [{"timestamp": "", "alert_type": "", "summary": "No alerts", "pcap": "", "alert_data": {}}]
