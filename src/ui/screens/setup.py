"""Setup guide screen for first run."""

from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from ..components import Card, PrimaryButton, SecondaryButton
from ..theme import Theme


class SetupScreen(Screen):
    """Screen with guided setup steps."""

    def __init__(self, app, theme: Theme, **kwargs) -> None:
        """Build the setup guide layout."""
        super().__init__(name="setup", **kwargs)
        self.app = app
        self.theme = theme

        root = BoxLayout(
            orientation="vertical",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )
        root.add_widget(self._header("Getting Started"))

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=theme.gap_m, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        guide_card = Card(
            theme,
            orientation="vertical",
            padding=theme.gap_m,
            spacing=theme.gap_s,
            size_hint_y=None,
        )
        guide_card.bind(minimum_height=guide_card.setter("height"))
        guide_card.add_widget(self._section_label("Step 1: Choose a Wi-Fi adapter"))
        guide_card.add_widget(
            self._body_label("Pick the adapter this device should listen on.")
        )
        self.interface_label = Label(
            text=self._interface_text(),
            color=self.theme.palette.text,
            font_size=self.theme.body,
            size_hint_y=None,
            height=self.theme.dp(24),
            halign="left",
            valign="middle",
        )
        self.interface_label.bind(size=lambda *_: setattr(self.interface_label, "text_size", self.interface_label.size))
        guide_card.add_widget(self.interface_label)
        open_network = SecondaryButton(theme, text="Open adapter settings")
        open_network.bind(on_press=lambda *_: self.app.show_screen("settings_network"))
        guide_card.add_widget(open_network)

        guide_card.add_widget(self._section_label("Step 2: Run device checks"))
        guide_card.add_widget(
            self._body_label("Check permissions, tools, battery, and adapter status.")
        )
        open_checks = SecondaryButton(theme, text="Open device checks")
        open_checks.bind(on_press=lambda *_: self.app.show_screen("diagnostics"))
        guide_card.add_widget(open_checks)

        guide_card.add_widget(self._section_label("Step 3: Start monitoring"))
        guide_card.add_widget(
            self._body_label(
                "Listening mode is passive only. The device never transmits or jams."
            )
        )
        start_now = PrimaryButton(theme, text="Start monitoring")
        start_now.bind(on_press=lambda *_: self._start_monitoring())
        guide_card.add_widget(start_now)

        guide_card.add_widget(
            self._body_label(
                "On Linux, monitoring still needs admin permissions (sudo or capabilities)."
            )
        )
        content.add_widget(guide_card)

        actions = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=theme.button_height,
            spacing=theme.gap_s,
        )
        finish_button = PrimaryButton(theme, text="Finish setup")
        skip_button = SecondaryButton(theme, text="Skip for now")
        finish_button.bind(on_press=lambda *_: self._finish_setup())
        skip_button.bind(on_press=lambda *_: self._finish_setup())
        actions.add_widget(finish_button)
        actions.add_widget(skip_button)
        content.add_widget(actions)

        hint = Label(
            text="You can reopen this guide from Settings.",
            color=self.theme.palette.text_dim,
            font_size=self.theme.caption,
            size_hint_y=None,
            height=self.theme.dp(18),
        )
        content.add_widget(hint)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

    def _header(self, title: str) -> BoxLayout:
        """Create a back header row."""
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=self.theme.nav_height,
            spacing=self.theme.gap_s,
        )
        back = SecondaryButton(self.theme, text="Back")
        back.size_hint_x = 0.2
        back.bind(on_press=lambda *_: self._finish_setup())
        label = Label(text=title, color=self.theme.palette.text, font_size=self.theme.h2, halign="left")
        label.bind(size=lambda *_: setattr(label, "text_size", label.size))
        row.add_widget(back)
        row.add_widget(label)
        return row

    def _section_label(self, text: str) -> Label:
        """Return a section title label."""
        return Label(
            text=text,
            color=self.theme.palette.text,
            font_size=self.theme.h3,
            size_hint_y=None,
            height=self.theme.dp(20),
        )

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

    def _interface_text(self) -> str:
        """Return the active interface label."""
        iface = self.app.interface_choice or "-"
        return f"Current adapter: {iface}"

    def _start_monitoring(self) -> None:
        """Start monitoring and return to dashboard."""
        self.app.start_monitoring()
        self.app.show_screen("dashboard")

    def _finish_setup(self) -> None:
        """Mark setup complete and return to dashboard."""
        self.app.mark_setup_complete()
        self.app.show_screen("dashboard")

    def refresh(self) -> None:
        """Refresh the interface label."""
        self.interface_label.text = self._interface_text()
