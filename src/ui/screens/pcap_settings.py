from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme
from ..widgets import Stepper


class PcapSettingsScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="pcap_settings", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )

        header = Label(text="PCAP Settings", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(28))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        evidence_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        evidence_card.add_widget(Label(text="Evidence & PCAP", color=theme.palette.text, font_size=theme.h3, size_hint_y=None, height=theme.dp(22)))
        evidence_card.add_widget(self._body_label("Tune session PCAP capture and retention limits for this device."))

        self.pcap_toggle = self._toggle_button(
            "PCAP capture: ON" if self.app.app_config.evidence.pcap_enabled else "PCAP capture: OFF",
            self.app.app_config.evidence.pcap_enabled,
            self._toggle_pcap,
        )
        evidence_card.add_widget(self.pcap_toggle)

        self.buffer_stepper = Stepper(
            theme,
            label="PCAP buffer (s)",
            value=int(self.app.app_config.evidence.pcap_buffer_seconds),
            step=5,
            on_change=self._update_buffer,
        )
        evidence_card.add_widget(self.buffer_stepper)

        self.max_files_stepper = Stepper(
            theme,
            label="Max PCAP files",
            value=int(self.app.app_config.evidence.pcap_max_files),
            step=10,
            on_change=self._update_max_files,
        )
        evidence_card.add_widget(self.max_files_stepper)

        self.max_mb_stepper = Stepper(
            theme,
            label="Max PCAP MB",
            value=int(self.app.app_config.evidence.pcap_max_total_mb),
            step=25,
            on_change=self._update_max_mb,
        )
        evidence_card.add_widget(self.max_mb_stepper)
        content.add_widget(evidence_card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        self.back_button = SecondaryButton(theme, text="Back to Settings")
        self.save_button = PrimaryButton(theme, text="Save")
        self.reset_button = SecondaryButton(theme, text="Reset")
        self.back_button.bind(on_press=lambda *_: self.app.show_screen("settings"))
        self.save_button.bind(on_press=lambda *_: self.app.persist_settings())
        self.reset_button.bind(on_press=lambda *_: self.app.reload_settings())
        actions.add_widget(self.back_button)
        actions.add_widget(self.save_button)
        actions.add_widget(self.reset_button)
        root.add_widget(actions)

        self.add_widget(root)

    def _body_label(self, text: str) -> Label:
        label = Label(
            text=text,
            color=self.theme.palette.text_dim,
            font_size=self.theme.body,
            size_hint_y=None,
            height=self.theme.dp(40),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        return label

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

    def _toggle_pcap(self, _instance) -> None:
        enabled = self.pcap_toggle.state == "down"
        self.pcap_toggle.text = "PCAP capture: ON" if enabled else "PCAP capture: OFF"
        self.app.app_config.evidence.pcap_enabled = enabled

    def _update_buffer(self, value: int) -> None:
        self.app.app_config.evidence.pcap_buffer_seconds = float(value)

    def _update_max_files(self, value: int) -> None:
        self.app.app_config.evidence.pcap_max_files = int(value)

    def _update_max_mb(self, value: int) -> None:
        self.app.app_config.evidence.pcap_max_total_mb = int(value)

    def refresh(self) -> None:
        self.pcap_toggle.state = "down" if self.app.app_config.evidence.pcap_enabled else "normal"
        self.pcap_toggle.text = "PCAP capture: ON" if self.app.app_config.evidence.pcap_enabled else "PCAP capture: OFF"
        self.buffer_stepper.value = int(self.app.app_config.evidence.pcap_buffer_seconds)
        self.buffer_stepper.value_label.text = str(self.buffer_stepper.value)
        self.max_files_stepper.value = int(self.app.app_config.evidence.pcap_max_files)
        self.max_files_stepper.value_label.text = str(self.max_files_stepper.value)
        self.max_mb_stepper.value = int(self.app.app_config.evidence.pcap_max_total_mb)
        self.max_mb_stepper.value_label.text = str(self.max_mb_stepper.value)
