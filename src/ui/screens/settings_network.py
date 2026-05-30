from __future__ import annotations

from typing import List

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme
from ...health import list_wireless_interfaces


class SettingsNetworkScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="settings_network", **kwargs)
        self.app = app
        self.theme = theme
        self._pending_interface = app.interface_choice or "wlan1"

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )
        root.add_widget(self._header("Wireless setup"))

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(self._section_label("Adapter"))
        card.add_widget(self._body_label("Choose the Wi-Fi adapter and listening mode."))

        self.interface_spinner = Spinner(
            text=self._pending_interface,
            values=self._interface_values(),
            size_hint_y=None,
            height=theme.button_height,
            background_normal="",
            background_color=theme.palette.surface_alt,
            color=theme.palette.text,
        )
        card.add_widget(self._field("Wi-Fi adapter", self.interface_spinner))

        self.monitor_toggle = self._toggle_button(
            "Listening mode: Auto-enable" if self.app.app_config.capture.enable_monitor else "Listening mode: Validate only",
            self.app.app_config.capture.enable_monitor,
            self._toggle_monitor,
        )
        card.add_widget(self.monitor_toggle)
        card.add_widget(self._body_label("Listening mode lets this device hear Wi-Fi management frames."))
        card.add_widget(self._body_label("On Linux you still need admin permissions (sudo or capabilities)."))
        content.add_widget(card)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        save_button = PrimaryButton(theme, text="Save")
        reset_button = SecondaryButton(theme, text="Reset")
        save_button.bind(on_press=lambda *_: self._save())
        reset_button.bind(on_press=lambda *_: self._reset())
        actions.add_widget(save_button)
        actions.add_widget(reset_button)
        content.add_widget(actions)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

    def _header(self, title: str) -> BoxLayout:
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.theme.nav_height, spacing=self.theme.gap_s)
        back = SecondaryButton(self.theme, text="Back")
        back.size_hint_x = 0.2
        back.bind(on_press=lambda *_: self.app.show_screen("settings"))
        label = Label(text=title, color=self.theme.palette.text, font_size=self.theme.h2, halign="left")
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        row.add_widget(back)
        row.add_widget(label)
        return row

    def _section_label(self, text: str) -> Label:
        label = Label(text=text, color=self.theme.palette.text, font_size=self.theme.h3, size_hint_y=None, height=self.theme.dp(20))
        return label

    def _body_label(self, text: str) -> Label:
        label = Label(
            text=text,
            color=self.theme.palette.text_dim,
            font_size=self.theme.body,
            size_hint_y=None,
            height=self.theme.dp(34),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        return label

    def _field(self, label_text: str, widget) -> BoxLayout:
        layout = BoxLayout(orientation="vertical", size_hint_y=None, height=self.theme.dp(64), spacing=self.theme.gap_xs)
        label = Label(
            text=label_text,
            color=self.theme.palette.text_dim,
            font_size=self.theme.caption,
            size_hint_y=None,
            height=self.theme.dp(18),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        layout.add_widget(label)
        layout.add_widget(widget)
        return layout

    def _toggle_button(self, text: str, enabled: bool, handler) -> ToggleButton:
        button = ToggleButton(
            text=text,
            state="down" if enabled else "normal",
            size_hint_y=None,
            height=self.theme.button_height,
            background_normal="",
            background_color=self.theme.palette.surface_alt,
            color=self.theme.palette.text,
        )
        button.bind(on_press=handler)
        return button

    def _interface_values(self) -> List[str]:
        values = []
        for name in list_wireless_interfaces():
            if name and name not in values:
                values.append(name)
        if self.app.interface_choice and self.app.interface_choice not in values:
            values.append(self.app.interface_choice)
        return values or ["wlan1"]

    def _toggle_monitor(self, _instance) -> None:
        enabled = self.monitor_toggle.state == "down"
        self.monitor_toggle.text = "Listening mode: Auto-enable" if enabled else "Listening mode: Validate only"
        self.app.app_config.capture.enable_monitor = enabled

    def _save(self) -> None:
        interface = (self.interface_spinner.text or "").strip() or "wlan1"
        self._pending_interface = interface
        self.app.interface_choice = interface
        self.app.app_config.capture.interface = interface
        self.app.persist_settings()

    def _reset(self) -> None:
        self.app.reload_settings()
        self.refresh()

    def refresh(self) -> None:
        self._pending_interface = self.app.interface_choice
        self.interface_spinner.values = self._interface_values()
        self.interface_spinner.text = self._pending_interface
        self.monitor_toggle.state = "down" if self.app.app_config.capture.enable_monitor else "normal"
        self.monitor_toggle.text = (
            "Listening mode: Auto-enable"
            if self.app.app_config.capture.enable_monitor
            else "Listening mode: Validate only"
        )
