from __future__ import annotations

import queue
from typing import Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager

from ..config import Config, load_config
from ..storage.db import get_setting, init_db, set_setting
from ..utils.logging import setup_logging
from ..battery_factory import build_battery_monitor
from ..health import list_wireless_interfaces
from .components import FooterNav, HeaderBar
from .controller import MonitorController
from .data import demo_alerts, demo_networks
from .onboarding import should_show_setup
from .screens.alerts import AlertsScreen
from .screens.dashboard import DashboardScreen
from .screens.diagnostics import DiagnosticsScreen
from .screens.networks import NetworksScreen
from .screens.settings import SettingsScreen
from .screens.settings_evidence import SettingsEvidenceScreen
from .screens.settings_network import SettingsNetworkScreen
from .screens.settings_system import SettingsSystemScreen
from .screens.setup import SetupScreen
from .state import AppState
from .theme import resolve_theme


class PWDBoxApp(App):
    def __init__(self, config: Config, demo: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app_config = config
        self.demo = demo
        self.event_queue: queue.Queue = queue.Queue()
        self.controller = MonitorController(self.app_config, self.event_queue)
        self.db_path = str(init_db(self.app_config.storage.db_path))
        self.state = AppState()
        self.theme_mode = "dark"
        self.theme = resolve_theme(self.theme_mode)
        self.interface_choice = self.app_config.capture.interface or "wlan1"
        self.battery_monitor = build_battery_monitor(demo=self.demo)
        self.setup_complete = False

        self.screen_manager: Optional[ScreenManager] = None
        self.header_bar: Optional[HeaderBar] = None
        self.footer_nav: Optional[FooterNav] = None
        self.dashboard: Optional[DashboardScreen] = None
        self.networks: Optional[NetworksScreen] = None
        self.alerts: Optional[AlertsScreen] = None
        self.settings: Optional[SettingsScreen] = None
        self.settings_network: Optional[SettingsNetworkScreen] = None
        self.settings_evidence: Optional[SettingsEvidenceScreen] = None
        self.settings_system: Optional[SettingsSystemScreen] = None
        self.diagnostics: Optional[DiagnosticsScreen] = None
        self.setup: Optional[SetupScreen] = None

        self.load_settings()

    def load_settings(self) -> None:
        default_interface = self.app_config.capture.interface or self.interface_choice or "wlan1"
        self.interface_choice = str(
            get_setting(
                "interface",
                get_setting("last_interface", default_interface, db_path=self.db_path),
                db_path=self.db_path,
            )
        )
        available = list_wireless_interfaces()
        if available and self.interface_choice not in available:
            self.interface_choice = available[0]
        self.app_config.capture.interface = self.interface_choice
        self.app_config.capture.enable_monitor = bool(
            get_setting("enable_monitor", self.app_config.capture.enable_monitor, db_path=self.db_path)
        )
        self.theme_mode = get_setting("theme_mode", "dark", db_path=self.db_path)
        self.app_config.evidence.pcap_enabled = bool(
            get_setting("pcap_enabled", self.app_config.evidence.pcap_enabled, db_path=self.db_path)
        )
        self.app_config.evidence.pcap_buffer_seconds = float(
            get_setting("pcap_buffer_seconds", self.app_config.evidence.pcap_buffer_seconds, db_path=self.db_path)
        )
        self.app_config.evidence.pcap_max_files = int(
            get_setting("pcap_max_files", self.app_config.evidence.pcap_max_files, db_path=self.db_path)
        )
        self.app_config.evidence.pcap_max_total_mb = int(
            get_setting("pcap_max_total_mb", self.app_config.evidence.pcap_max_total_mb, db_path=self.db_path)
        )
        self.setup_complete = bool(get_setting("setup_complete", False, db_path=self.db_path))
        self.theme = resolve_theme(self.theme_mode)

    def persist_settings(self) -> None:
        set_setting("interface", self.interface_choice, db_path=self.db_path)
        set_setting("last_interface", self.interface_choice, db_path=self.db_path)
        set_setting("enable_monitor", self.app_config.capture.enable_monitor, db_path=self.db_path)
        set_setting("pcap_enabled", self.app_config.evidence.pcap_enabled, db_path=self.db_path)
        set_setting("pcap_buffer_seconds", self.app_config.evidence.pcap_buffer_seconds, db_path=self.db_path)
        set_setting("pcap_max_files", self.app_config.evidence.pcap_max_files, db_path=self.db_path)
        set_setting("pcap_max_total_mb", self.app_config.evidence.pcap_max_total_mb, db_path=self.db_path)
        set_setting("theme_mode", self.theme_mode, db_path=self.db_path)
        if self.header_bar:
            self.header_bar.set_message("Settings saved")

    def reload_settings(self) -> None:
        self.load_settings()
        if self.settings:
            self.settings.refresh()
        if self.settings_network:
            self.settings_network.refresh()
        if self.settings_evidence:
            self.settings_evidence.refresh()
        if self.settings_system:
            self.settings_system.refresh()
        if self.setup:
            self.setup.refresh()
        if self.header_bar:
            self.header_bar.set_message("Settings reloaded")

    def mark_setup_complete(self) -> None:
        self.setup_complete = True
        set_setting("setup_complete", True, db_path=self.db_path)

    def set_theme(self, mode: str) -> None:
        previous_screen = None
        if self.screen_manager:
            previous_screen = self.screen_manager.current
        self.theme_mode = mode
        set_setting("theme_mode", mode, db_path=self.db_path)
        self.theme = resolve_theme(self.theme_mode)
        Window.clearcolor = self.theme.palette.background

        # Recompose the UI so theme changes are visible immediately.
        if self.root:
            self.root.clear_widgets()
            self._compose_root(self.root)
            if previous_screen and self.screen_manager:
                self.screen_manager.current = previous_screen

        if self.header_bar:
            self.header_bar.set_message("Theme updated")

    def _compose_root(self, root: BoxLayout) -> None:
        self.header_bar = HeaderBar(self.theme, title="PWD-Box")
        root.add_widget(self.header_bar)

        self.screen_manager = ScreenManager()
        self.dashboard = DashboardScreen(self, self.theme)
        self.networks = NetworksScreen(self, self.theme)
        self.alerts = AlertsScreen(self, self.theme)
        self.settings = SettingsScreen(self, self.theme)
        self.settings_network = SettingsNetworkScreen(self, self.theme)
        self.settings_evidence = SettingsEvidenceScreen(self, self.theme)
        self.settings_system = SettingsSystemScreen(self, self.theme)
        self.diagnostics = DiagnosticsScreen(self, self.theme)
        self.setup = SetupScreen(self, self.theme)

        self.screen_manager.add_widget(self.dashboard)
        self.screen_manager.add_widget(self.networks)
        self.screen_manager.add_widget(self.alerts)
        self.screen_manager.add_widget(self.settings)
        self.screen_manager.add_widget(self.settings_network)
        self.screen_manager.add_widget(self.settings_evidence)
        self.screen_manager.add_widget(self.settings_system)
        self.screen_manager.add_widget(self.diagnostics)
        self.screen_manager.add_widget(self.setup)

        root.add_widget(self.screen_manager)

        self.footer_nav = FooterNav(self.theme, self.screen_manager)
        root.add_widget(self.footer_nav)
        self.refresh_battery_status(0)

    def build(self):
        self.theme = resolve_theme(self.theme_mode)
        Window.clearcolor = self.theme.palette.background
        root = BoxLayout(orientation="vertical")
        self._compose_root(root)
        return root

    def on_start(self) -> None:
        Clock.schedule_interval(self.process_queue, 0.25)
        Clock.schedule_interval(self.refresh_history, 5.0)
        Clock.schedule_interval(self.refresh_battery_status, 10.0)
        if self.networks:
            self.networks.update_status(self.state.status, self.state.running, self.state.last_error)
        if self.demo:
            Clock.schedule_interval(self._demo_tick, 1.0)
        if self.screen_manager and should_show_setup(self.demo, self.setup_complete):
            self.show_screen("setup")

    def start_monitoring(self) -> None:
        self.header_bar.set_message(None)
        self.state.status = {
            "adapter_ok": False,
            "monitor_mode": False,
            "logging_on": False,
            "running": False,
            "interface": self.interface_choice,
            "message": None,
        }
        self.state.networks = []
        self.state.alerts = []
        self.state.session_alert_count = 0
        self.state.last_alert_time = None
        self.state.last_error = None
        if self.networks:
            self.networks.update_networks(self.state.networks)
            self.networks.update_status(self.state.status, self.state.running, self.state.last_error)
        self.controller.start(interface=self.interface_choice)

    def stop_monitoring(self) -> None:
        self.controller.stop()

    def show_screen(self, name: str) -> None:
        if self.screen_manager:
            self.screen_manager.current = name
        if name == "settings" and self.settings:
            self.settings.refresh()
        if name == "settings_network" and self.settings_network:
            self.settings_network.refresh()
        if name == "settings_evidence" and self.settings_evidence:
            self.settings_evidence.refresh()
        if name == "settings_system" and self.settings_system:
            self.settings_system.refresh()
        if name == "alerts" and self.alerts:
            self.alerts.refresh_history()
        if name == "setup" and self.setup:
            self.setup.refresh()

    def process_queue(self, _dt) -> None:
        updated_networks = False
        updated_alerts = False
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                break

            event_type = event.get("type")
            data = event.get("data", {})
            if event_type == "status":
                self.state.status = data
                self.state.running = bool(data.get("running"))
                message = data.get("message")
                self.state.last_error = message if message else None
            elif event_type == "networks":
                self.state.networks = data.get("items", [])
                updated_networks = True
            elif event_type == "alert":
                self.state.alerts.insert(0, data)
                self.state.alerts = self.state.alerts[:50]
                self.state.last_alert_time = data.get("timestamp")
                self.state.session_alert_count += 1
                updated_alerts = True
            elif event_type == "stopped":
                self.state.running = False

        self._update_dashboard()
        if self.networks:
            if updated_networks:
                self.networks.update_networks(self.state.networks)
            self.networks.update_status(self.state.status, self.state.running, self.state.last_error)
        if updated_alerts and self.alerts:
            self.alerts.update_alerts(self.state.alerts)

    def refresh_battery_status(self, _dt) -> None:
        if not self.header_bar:
            return
        self.header_bar.update_battery(self.battery_monitor.read_snapshot())

    def _update_dashboard(self) -> None:
        if not self.dashboard or not self.header_bar:
            return
        status = self.state.status
        if self.controller.is_running():
            if status.get("message"):
                state_text = "ERROR"
                tone = "error"
            elif status.get("adapter_ok") and status.get("monitor_mode"):
                state_text = "RUNNING"
                tone = "ok"
            else:
                state_text = "STARTING"
                tone = "warn"
        else:
            if self.state.last_error:
                state_text = "ERROR"
                tone = "error"
            else:
                state_text = "STOPPED"
                tone = "neutral"

        self.header_bar.update_status(state_text, tone)
        self.header_bar.set_message(self.state.last_error)
        self.dashboard.update_status(status, state_text, tone)
        self.dashboard.update_alert_summary(self.state.last_alert_time, self.state.session_alert_count)

        if self.state.last_error:
            self.dashboard.show_alert_banner(self.state.last_error)
        elif self.state.alerts:
            latest = self.state.alerts[0]
            banner_text = f"Alert: {latest.get('alert_type')} {latest.get('key')}"
            self.dashboard.show_alert_banner(banner_text)
        else:
            self.dashboard.show_alert_banner(None)

    def refresh_history(self, _dt) -> None:
        if self.screen_manager and self.screen_manager.current != "alerts":
            return
        if self.alerts:
            self.alerts.refresh_history()

    def _demo_tick(self, _dt) -> None:
        self.state.status.update(
            {
                "running": True,
                "adapter_ok": True,
                "monitor_mode": True,
                "logging_on": True,
                "interface": self.interface_choice,
            }
        )
        self.state.networks = demo_networks()
        self.state.alerts = demo_alerts()
        self.state.last_alert_time = self.state.alerts[0].get("timestamp") if self.state.alerts else None
        self.state.session_alert_count = len(self.state.alerts)
        self._update_dashboard()
        if self.networks:
            self.networks.update_networks(self.state.networks)
        if self.alerts:
            self.alerts.update_alerts(self.state.alerts)

    def on_stop(self) -> None:
        self.controller.stop()


def run_ui(config_path: Optional[str] = None, demo: bool = False) -> int:
    config = load_config(config_path)
    setup_logging(config.logging.level)
    app = PWDBoxApp(config, demo=demo)
    app.run()
    return 0
