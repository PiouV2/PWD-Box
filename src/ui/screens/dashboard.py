from __future__ import annotations

from typing import Any, Dict, Optional

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from ..components import AlertBanner, Card, PrimaryButton, SecondaryButton, StatusChip
from ..theme import Theme


class DashboardScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="dashboard", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )

        self.alert_banner = AlertBanner(theme)
        root.add_widget(self.alert_banner)

        body = BoxLayout(orientation="horizontal", spacing=theme.gap_m, size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))

        self.status_card = Card(
            theme,
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_s, theme.gap_m, theme.gap_s],
            spacing=theme.gap_xs,
        )
        self.status_card.size_hint_x = 0.52
        self.status_card.size_hint_y = None
        self.status_card.bind(minimum_height=self.status_card.setter("height"))

        title = Label(text="Device status", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24))
        self.status_card.add_widget(title)

        self.monitoring_chip = StatusChip(theme)
        self.monitoring_chip.text = "STOPPED"
        self.monitoring_chip.tone = "neutral"
        self.status_card.add_widget(self._row("Listening", chip=self.monitoring_chip))

        self.interface_label = Label(text="-", color=theme.palette.text, font_size=theme.body)
        self.status_card.add_widget(self._row("Interface", value_widget=self.interface_label))

        self.monitor_mode_label = Label(text="OFF", color=theme.palette.text, font_size=theme.body)
        self.status_card.add_widget(self._row("Listening mode", value_widget=self.monitor_mode_label))

        self.logging_label = Label(text="OFF", color=theme.palette.text, font_size=theme.body)
        self.status_card.add_widget(self._row("Recording", value_widget=self.logging_label))

        self.last_alert_label = Label(text="-", color=theme.palette.text, font_size=theme.body)
        self.status_card.add_widget(self._row("Last alert", value_widget=self.last_alert_label))

        self.alert_count_label = Label(text="0", color=theme.palette.text, font_size=theme.body)
        self.status_card.add_widget(self._row("Alerts (session)", value_widget=self.alert_count_label))

        body.add_widget(self.status_card)

        actions = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_m)
        actions.size_hint_x = 0.48
        actions.size_hint_y = None
        actions.bind(minimum_height=actions.setter("height"))
        actions_title = Label(text="Start monitoring", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24))
        actions.add_widget(actions_title)

        actions_hint = Label(
            text="Tap Start to begin listening.",
            color=theme.palette.text_dim,
            font_size=theme.caption,
            size_hint_y=None,
            height=theme.dp(18),
        )
        actions.add_widget(actions_hint)

        grid = GridLayout(cols=2, spacing=theme.gap_s, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        self.start_button = PrimaryButton(theme, text="Start monitoring")
        self.stop_button = SecondaryButton(theme, text="Stop")
        self.start_button.height = theme.button_height
        self.stop_button.height = theme.button_height
        self.start_button.bind(on_press=lambda *_: self.app.start_monitoring())
        self.stop_button.bind(on_press=lambda *_: self.app.stop_monitoring())

        grid.add_widget(self.start_button)
        grid.add_widget(self.stop_button)

        for label, target in (
            ("Alerts", "alerts"),
            ("Networks", "networks"),
            ("Settings", "settings"),
            ("Evidence", "settings_evidence"),
            ("Setup", "setup"),
        ):
            button = SecondaryButton(theme, text=label)
            button.height = theme.button_height
            button.bind(on_press=lambda *_x, name=target: self.app.show_screen(name))
            grid.add_widget(button)

        actions.add_widget(grid)
        body.add_widget(actions)

        body_container = AnchorLayout(anchor_x="center", anchor_y="center")
        body_container.add_widget(body)
        root.add_widget(body_container)
        self.add_widget(root)

    def _row(
        self,
        label: str,
        value_widget: Optional[Label] = None,
        chip: Optional[StatusChip] = None,
    ) -> BoxLayout:
        row = BoxLayout(orientation="horizontal", spacing=self.theme.gap_s, size_hint_y=None, height=self.theme.dp(26))
        row.add_widget(Label(text=label, color=self.theme.palette.text_dim, font_size=self.theme.body, size_hint_x=0.55))
        if chip is not None:
            chip.size_hint_x = 0.45
            row.add_widget(chip)
        elif value_widget is not None:
            value_widget.size_hint_x = 0.45
            row.add_widget(value_widget)
        return row

    def update_status(self, status: Dict[str, Any], state_text: str, tone: str) -> None:
        self.monitoring_chip.text = state_text
        self.monitoring_chip.tone = tone
        interface = status.get("interface") or self.app.interface_choice or "-"
        self.interface_label.text = interface
        self.monitor_mode_label.text = "ON" if status.get("monitor_mode") else "OFF"
        evidence_active = bool(status.get("evidence_active", status.get("logging_on")))
        self.logging_label.text = "ON" if evidence_active else "OFF"

    def update_alert_summary(self, last_alert_time: Optional[str], count: int) -> None:
        self.last_alert_label.text = last_alert_time or "-"
        self.alert_count_label.text = str(count)

    def show_alert_banner(self, message: Optional[str], tone: str = "warn") -> None:
        if message:
            self.alert_banner.show(message, tone=tone)
        else:
            self.alert_banner.hide()
