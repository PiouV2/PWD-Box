from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme
from ..widgets import Stepper


class SettingsEvidenceScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="settings_evidence", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )
        root.add_widget(self._header("Evidence (PCAP)"))

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        evidence_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        evidence_card.add_widget(self._section_label("Capture"))
        evidence_card.add_widget(self._body_label("Tune alert PCAP capture and retention limits."))

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

        evidence_card.add_widget(self._field("PCAP path", self._value_label(self._pcap_path())))
        content.add_widget(evidence_card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        save_button = PrimaryButton(theme, text="Save")
        reset_button = SecondaryButton(theme, text="Reset")
        save_button.bind(on_press=lambda *_: self._save())
        reset_button.bind(on_press=lambda *_: self._reset())
        actions.add_widget(save_button)
        actions.add_widget(reset_button)
        root.add_widget(actions)

        self.add_widget(root)

    def _header(self, title: str) -> BoxLayout:
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=self.theme.button_height, spacing=self.theme.gap_s)
        back = SecondaryButton(self.theme, text="Back")
        back.size_hint_x = 0.2
        back.bind(on_press=lambda *_: self.app.show_screen("settings"))
        label = Label(text=title, color=self.theme.palette.text, font_size=self.theme.h2, halign="left")
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        row.add_widget(back)
        row.add_widget(label)
        return row

    def _section_label(self, text: str) -> Label:
        label = Label(text=text, color=self.theme.palette.text, font_size=self.theme.h3, size_hint_y=None, height=self.theme.dp(22))
        return label

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

    def _field(self, label_text: str, widget) -> BoxLayout:
        layout = BoxLayout(orientation="vertical", size_hint_y=None, height=self.theme.dp(76), spacing=self.theme.gap_xs)
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

    def _value_label(self, value: str) -> Label:
        label = Label(
            text=value,
            color=self.theme.palette.text,
            font_size=self.theme.body,
            size_hint_y=None,
            height=self.theme.dp(32),
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

    def _pcap_path(self) -> str:
        return self.app.app_config.evidence.pcap_dir or "data/pcaps"

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

    def _save(self) -> None:
        self.app.persist_settings()

    def _reset(self) -> None:
        self.app.reload_settings()
        self.refresh()

    def refresh(self) -> None:
        self.pcap_toggle.state = "down" if self.app.app_config.evidence.pcap_enabled else "normal"
        self.pcap_toggle.text = "PCAP capture: ON" if self.app.app_config.evidence.pcap_enabled else "PCAP capture: OFF"
        self.buffer_stepper.value = int(self.app.app_config.evidence.pcap_buffer_seconds)
        self.buffer_stepper.value_label.text = str(self.buffer_stepper.value)
        self.max_files_stepper.value = int(self.app.app_config.evidence.pcap_max_files)
        self.max_files_stepper.value_label.text = str(self.max_files_stepper.value)
        self.max_mb_stepper.value = int(self.app.app_config.evidence.pcap_max_total_mb)
        self.max_mb_stepper.value_label.text = str(self.max_mb_stepper.value)
