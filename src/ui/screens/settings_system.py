from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.togglebutton import ToggleButton

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme


class SettingsSystemScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="settings_system", **kwargs)
        self.app = app
        self.theme = theme
        self._pending_theme_mode = self.app.theme_mode

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )
        root.add_widget(self._header("System"))

        tools_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        tools_card.bind(minimum_height=tools_card.setter("height"))
        tools_card.add_widget(self._section_label("Display & Tools"))
        tools_card.add_widget(self._body_label("Theme and diagnostics controls."))

        self.theme_toggle = self._toggle_button(
            "Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light",
            self.app.theme_mode == "dark",
            self._toggle_theme,
        )
        tools_card.add_widget(self.theme_toggle)

        self.health_button = SecondaryButton(theme, text="Open Health Checks")
        self.health_button.size_hint_y = None
        self.health_button.height = theme.button_height
        self.health_button.bind(on_press=lambda *_: self.app.show_screen("diagnostics"))
        tools_card.add_widget(self.health_button)
        root.add_widget(tools_card)

        paths_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        paths_card.bind(minimum_height=paths_card.setter("height"))
        paths_card.add_widget(self._section_label("Paths"))
        paths_card.add_widget(self._field("Database path", self._value_label(self.app.db_path)))
        paths_card.add_widget(self._field("Logging level", self._value_label(self.app.app_config.logging.level)))
        root.add_widget(paths_card)

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
        return Label(text=text, color=self.theme.palette.text, font_size=self.theme.h3, size_hint_y=None, height=self.theme.dp(20))

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

    def _toggle_theme(self, _instance) -> None:
        self._pending_theme_mode = "dark" if self.theme_toggle.state == "down" else "light"
        self.theme_toggle.text = "Theme: Dark" if self._pending_theme_mode == "dark" else "Theme: Light"

    def _save(self) -> None:
        self.app.set_theme(self._pending_theme_mode)
        self.app.persist_settings()

    def _reset(self) -> None:
        self.app.reload_settings()
        self.refresh()

    def refresh(self) -> None:
        self._pending_theme_mode = self.app.theme_mode
        self.theme_toggle.state = "down" if self.app.theme_mode == "dark" else "normal"
        self.theme_toggle.text = "Theme: Dark" if self.app.theme_mode == "dark" else "Theme: Light"
