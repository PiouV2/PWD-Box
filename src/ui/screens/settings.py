from __future__ import annotations

from typing import Callable

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme


class Stepper(BoxLayout):
    def __init__(self, theme: Theme, label: str, value: int, step: int, on_change: Callable[[int], None], **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s, **kwargs)
        self.theme = theme
        self.value = value
        self.step = step
        self.on_change = on_change

        self.label = Label(text=label, color=theme.palette.text, font_size=theme.body, size_hint_x=0.5)
        self.value_label = Label(text=str(value), color=theme.palette.text, font_size=theme.body, size_hint_x=0.2)
        self.minus = SecondaryButton(theme, text="-")
        self.plus = SecondaryButton(theme, text="+")
        self.minus.bind(on_press=lambda *_: self._update(-self.step))
        self.plus.bind(on_press=lambda *_: self._update(self.step))
        self.add_widget(self.label)
        self.add_widget(self.minus)
        self.add_widget(self.value_label)
        self.add_widget(self.plus)

    def _update(self, delta: int) -> None:
        self.value = max(0, self.value + delta)
        self.value_label.text = str(self.value)
        self.on_change(self.value)


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

        interface_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        interface_card.add_widget(Label(text="Interface", color=theme.palette.text, font_size=theme.h3, size_hint_y=None, height=theme.dp(22)))
        self.interface_spinner = Spinner(
            text=self.app.interface_choice or "wlan0",
            values=["wlan0", "wlan1"],
            size_hint_y=None,
            height=theme.button_height,
        )
        interface_card.add_widget(self.interface_spinner)
        root.add_widget(interface_card)

        evidence_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        evidence_card.add_widget(Label(text="Evidence", color=theme.palette.text, font_size=theme.h3, size_hint_y=None, height=theme.dp(22)))

        self.pcap_toggle = ToggleButton(
            text="PCAP capture: ON" if self.app.config.evidence.pcap_enabled else "PCAP capture: OFF",
            state="down" if self.app.config.evidence.pcap_enabled else "normal",
            size_hint_y=None,
            height=theme.button_height,
            background_normal="",
            background_color=theme.palette.surface_alt,
            color=theme.palette.text,
        )
        self.pcap_toggle.bind(on_press=self._toggle_pcap)
        evidence_card.add_widget(self.pcap_toggle)

        self.buffer_stepper = Stepper(
            theme,
            label="PCAP buffer (s)",
            value=int(self.app.config.evidence.pcap_buffer_seconds),
            step=5,
            on_change=self._update_buffer,
        )
        evidence_card.add_widget(self.buffer_stepper)

        self.max_files_stepper = Stepper(
            theme,
            label="Max PCAP files",
            value=int(self.app.config.evidence.pcap_max_files),
            step=10,
            on_change=self._update_max_files,
        )
        evidence_card.add_widget(self.max_files_stepper)

        self.max_mb_stepper = Stepper(
            theme,
            label="Max PCAP MB",
            value=int(self.app.config.evidence.pcap_max_total_mb),
            step=25,
            on_change=self._update_max_mb,
        )
        evidence_card.add_widget(self.max_mb_stepper)
        root.add_widget(evidence_card)

        ui_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        ui_card.add_widget(Label(text="UI", color=theme.palette.text, font_size=theme.h3, size_hint_y=None, height=theme.dp(22)))
        self.theme_toggle = ToggleButton(
            text="Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light",
            state="down" if self.app.theme_mode == "dark" else "normal",
            size_hint_y=None,
            height=theme.button_height,
            background_normal="",
            background_color=theme.palette.surface_alt,
            color=theme.palette.text,
        )
        self.theme_toggle.bind(on_press=self._toggle_theme)
        ui_card.add_widget(self.theme_toggle)
        root.add_widget(ui_card)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        self.save_button = PrimaryButton(theme, text="Save")
        self.reset_button = SecondaryButton(theme, text="Reset")
        self.save_button.bind(on_press=lambda *_: self._save())
        self.reset_button.bind(on_press=lambda *_: self.app.reload_settings())
        actions.add_widget(self.save_button)
        actions.add_widget(self.reset_button)
        root.add_widget(actions)

        self.add_widget(root)

    def _toggle_pcap(self, _instance) -> None:
        enabled = self.pcap_toggle.state == "down"
        self.pcap_toggle.text = "PCAP capture: ON" if enabled else "PCAP capture: OFF"
        self.app.config.evidence.pcap_enabled = enabled

    def _update_buffer(self, value: int) -> None:
        self.app.config.evidence.pcap_buffer_seconds = float(value)

    def _update_max_files(self, value: int) -> None:
        self.app.config.evidence.pcap_max_files = int(value)

    def _update_max_mb(self, value: int) -> None:
        self.app.config.evidence.pcap_max_total_mb = int(value)

    def _toggle_theme(self, _instance) -> None:
        mode = "dark" if self.theme_toggle.state == "down" else "light"
        self.theme_toggle.text = "Theme: Dark" if mode == "dark" else "Theme: Light"
        self.app.set_theme(mode)

    def _save(self) -> None:
        self.app.interface_choice = self.interface_spinner.text
        self.app.config.capture.interface = self.app.interface_choice
        self.app.persist_settings()

    def refresh(self) -> None:
        self.interface_spinner.text = self.app.interface_choice or "wlan0"
        self.pcap_toggle.state = "down" if self.app.config.evidence.pcap_enabled else "normal"
        self.pcap_toggle.text = "PCAP capture: ON" if self.app.config.evidence.pcap_enabled else "PCAP capture: OFF"
        self.buffer_stepper.value = int(self.app.config.evidence.pcap_buffer_seconds)
        self.buffer_stepper.value_label.text = str(self.buffer_stepper.value)
        self.max_files_stepper.value = int(self.app.config.evidence.pcap_max_files)
        self.max_files_stepper.value_label.text = str(self.max_files_stepper.value)
        self.max_mb_stepper.value = int(self.app.config.evidence.pcap_max_total_mb)
        self.max_mb_stepper.value_label.text = str(self.max_mb_stepper.value)
        self.theme_toggle.state = "down" if self.app.theme_mode == "dark" else "normal"
        self.theme_toggle.text = "Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light"
