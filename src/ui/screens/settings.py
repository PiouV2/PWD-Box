from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme
from ..widgets import Stepper


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

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        capture_card = self._section_card(
            "Capture",
            "Choose the interface used by the shared monitor backend and whether the UI should try to enable monitor mode.",
        )
        self.interface_input = TextInput(
            text=self.app.interface_choice,
            multiline=False,
            size_hint_y=None,
            height=theme.button_height,
            background_normal="",
            background_active="",
            background_color=theme.palette.surface_alt,
            foreground_color=theme.palette.text,
            cursor_color=theme.palette.text,
            padding=[theme.gap_s, theme.gap_s, theme.gap_s, theme.gap_s],
        )
        capture_card.add_widget(self._field("Capture interface", self.interface_input))
        self.monitor_toggle = self._toggle_button(
            "Monitor mode: Auto-enable" if self.app.app_config.capture.enable_monitor else "Monitor mode: Validate only",
            self.app.app_config.capture.enable_monitor,
            self._toggle_monitor,
        )
        capture_card.add_widget(self.monitor_toggle)
        capture_card.add_widget(
            self._body_label("Passive capture still needs sudo or CAP_NET_ADMIN/CAP_NET_RAW on the device.")
        )
        content.add_widget(capture_card)

        appearance_card = self._section_card(
            "Display",
            "Theme controls stay separate from capture settings so operational changes are easy to spot.",
        )
        self.theme_toggle = self._toggle_button(
            "Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light",
            self.app.theme_mode == "dark",
            self._toggle_theme,
        )
        appearance_card.add_widget(self.theme_toggle)
        content.add_widget(appearance_card)

        tools_card = self._section_card(
            "Tools",
            "Open diagnostics and evidence controls from here.",
        )
        nav_actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        self.pcap_settings_button = SecondaryButton(theme, text="PCAP Settings")
        self.health_button = SecondaryButton(theme, text="Health Checks")
        self.pcap_settings_button.bind(on_press=lambda *_: self.app.show_screen("pcap_settings"))
        self.health_button.bind(on_press=lambda *_: self.app.show_screen("diagnostics"))
        nav_actions.add_widget(self.pcap_settings_button)
        nav_actions.add_widget(self.health_button)
        tools_card.add_widget(nav_actions)
        content.add_widget(tools_card)

        scroll.add_widget(content)
        root.add_widget(scroll)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.button_height, spacing=theme.gap_s)
        self.save_button = PrimaryButton(theme, text="Save")
        self.reset_button = SecondaryButton(theme, text="Reset")
        self.save_button.bind(on_press=lambda *_: self._save())
        self.reset_button.bind(on_press=lambda *_: self.app.reload_settings())
        actions.add_widget(self.save_button)
        actions.add_widget(self.reset_button)
        root.add_widget(actions)

        self.add_widget(root)

    def _section_card(self, title: str, description: str) -> Card:
        card = Card(self.theme, orientation="vertical", padding=self.theme.gap_m, spacing=self.theme.gap_s)
        card.add_widget(
            Label(
                text=title,
                color=self.theme.palette.text,
                font_size=self.theme.h3,
                size_hint_y=None,
                height=self.theme.dp(22),
            )
        )
        card.add_widget(self._body_label(description))
        return card

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

    def _toggle_monitor(self, _instance) -> None:
        enabled = self.monitor_toggle.state == "down"
        self.monitor_toggle.text = "Monitor mode: Auto-enable" if enabled else "Monitor mode: Validate only"
        self.app.app_config.capture.enable_monitor = enabled

    def _toggle_theme(self, _instance) -> None:
        mode = "dark" if self.theme_toggle.state == "down" else "light"
        self.theme_toggle.text = "Theme: Dark" if mode == "dark" else "Theme: Light"
        self.app.set_theme(mode)

    def _save(self) -> None:
        entered_interface = self.interface_input.text.strip()
        configured_interface = self.app.app_config.capture.interface
        interface = entered_interface or configured_interface or "wlan1"
        self.interface_input.text = interface
        self.app.interface_choice = interface
        self.app.app_config.capture.interface = interface
        self.app.persist_settings()

    def refresh(self) -> None:
        self.interface_input.text = self.app.interface_choice
        self.monitor_toggle.state = "down" if self.app.app_config.capture.enable_monitor else "normal"
        self.monitor_toggle.text = (
            "Monitor mode: Auto-enable"
            if self.app.app_config.capture.enable_monitor
            else "Monitor mode: Validate only"
        )
        self.theme_toggle.state = "down" if self.app.theme_mode == "dark" else "normal"
        self.theme_toggle.text = "Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light"
