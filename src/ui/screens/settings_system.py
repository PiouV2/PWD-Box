"""System settings screen."""

from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme


class SettingsSystemScreen(Screen):
    """Screen for theme and system tools."""

    def __init__(self, app, theme: Theme, **kwargs) -> None:
        """Build the system settings layout."""
        super().__init__(name="settings_system", **kwargs)
        self.app = app
        self.theme = theme
        self._pending_theme_mode = self.app.theme_mode or "dark"

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )
        root.add_widget(self._header("Device"))

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        tools_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        tools_card.bind(minimum_height=tools_card.setter("height"))
        tools_card.add_widget(self._section_label("Display and tools"))
        tools_card.add_widget(self._body_label("Device checks and storage settings."))

        self.theme_button = SecondaryButton(theme, text=self._theme_button_text())
        self.theme_button.size_hint_y = None
        self.theme_button.height = theme.button_height
        self.theme_button.bind(on_press=lambda *_: self._toggle_theme())
        tools_card.add_widget(self.theme_button)

        self.health_button = SecondaryButton(theme, text="Open device checks")
        self.health_button.size_hint_y = None
        self.health_button.height = theme.button_height
        self.health_button.bind(on_press=lambda *_: self.app.show_screen("diagnostics"))
        tools_card.add_widget(self.health_button)
        content.add_widget(tools_card)

        paths_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        paths_card.bind(minimum_height=paths_card.setter("height"))
        paths_card.add_widget(self._section_label("Storage"))
        paths_card.add_widget(self._field("Database file", self._value_label(self.app.db_path)))
        paths_card.add_widget(self._field("Logging level (advanced)", self._value_label(self.app.app_config.logging.level)))
        content.add_widget(paths_card)

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
        """Create a back header row."""
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
        """Return a section title label."""
        return Label(text=text, color=self.theme.palette.text, font_size=self.theme.h3, size_hint_y=None, height=self.theme.dp(20))

    def _body_label(self, text: str) -> Label:
        """Return a helper text label."""
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
        """Create a labeled field container."""
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
        """Return a value label used in read-only fields."""
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

    def _save(self) -> None:
        """Persist theme changes and settings."""
        self.app.set_theme(self._pending_theme_mode)
        self.app.persist_settings()

    def _reset(self) -> None:
        """Reload settings and refresh fields."""
        self.app.reload_settings()
        self.refresh()

    def _theme_button_text(self) -> str:
        """Return the theme button label based on state."""
        if self._pending_theme_mode == "dark":
            return "Theme: Dark (tap for Light)"
        return "Theme: Light (tap for Dark)"

    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme previews."""
        self._pending_theme_mode = "light" if self._pending_theme_mode == "dark" else "dark"
        self.theme_button.text = self._theme_button_text()

    def refresh(self) -> None:
        """Refresh UI widgets from current config values."""
        self._pending_theme_mode = self.app.theme_mode or "dark"
        self.theme_button.text = self._theme_button_text()
