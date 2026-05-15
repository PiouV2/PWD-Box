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
from .components import FooterNav, HeaderBar
from .controller import MonitorController
from .data import demo_alerts, demo_networks
from .screens.alerts import AlertsScreen
from .screens.dashboard import DashboardScreen
from .screens.diagnostics import DiagnosticsScreen
from .screens.history import HistoryScreen
from .screens.networks import NetworksScreen
from .screens.settings import SettingsScreen
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
        self.interface_choice = "wlan1"
        self.network_filter_mode = "all"

        self.screen_manager: Optional[ScreenManager] = None
        self.header_bar: Optional[HeaderBar] = None
        self.footer_nav: Optional[FooterNav] = None
        self.dashboard: Optional[DashboardScreen] = None
        self.networks: Optional[NetworksScreen] = None
        self.alerts: Optional[AlertsScreen] = None
        self.history: Optional[HistoryScreen] = None
        self.settings: Optional[SettingsScreen] = None
        self.diagnostics: Optional[DiagnosticsScreen] = None

        self.load_settings()

    def load_settings(self) -> None:
        self.interface_choice = "wlan1"
        self.app_config.capture.interface = self.interface_choice
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
        self.network_filter_mode = "all"
        self.controller.set_network_filter_mode(self.network_filter_mode)
        self.theme = resolve_theme(self.theme_mode)

    def persist_settings(self) -> None:
        set_setting("interface", self.interface_choice, db_path=self.db_path)
        set_setting("last_interface", self.interface_choice, db_path=self.db_path)
        set_setting("pcap_enabled", self.app_config.evidence.pcap_enabled, db_path=self.db_path)
        set_setting("pcap_buffer_seconds", self.app_config.evidence.pcap_buffer_seconds, db_path=self.db_path)
        set_setting("pcap_max_files", self.app_config.evidence.pcap_max_files, db_path=self.db_path)
        set_setting("pcap_max_total_mb", self.app_config.evidence.pcap_max_total_mb, db_path=self.db_path)
        set_setting("network_filter_mode", "all", db_path=self.db_path)
        set_setting("theme_mode", self.theme_mode, db_path=self.db_path)
        if self.header_bar:
            self.header_bar.set_message("Settings saved")

    def reload_settings(self) -> None:
        self.load_settings()
        if self.settings:
            self.settings.refresh()
        if self.header_bar:
            self.header_bar.set_message("Settings reloaded")

    def set_theme(self, mode: str) -> None:
        self.theme_mode = mode
        set_setting("theme_mode", mode, db_path=self.db_path)
        if self.header_bar:
            self.header_bar.set_message("Theme saved. Restart UI to apply.")

    def build(self):
        self.theme = resolve_theme(self.theme_mode)
        Window.clearcolor = self.theme.palette.background
        root = BoxLayout(orientation="vertical")

        self.header_bar = HeaderBar(self.theme, title="PWD-Box")
        root.add_widget(self.header_bar)

        self.screen_manager = ScreenManager()
        self.dashboard = DashboardScreen(self, self.theme)
        self.networks = NetworksScreen(self, self.theme)
        self.alerts = AlertsScreen(self, self.theme)
        self.history = HistoryScreen(self, self.theme)
        self.settings = SettingsScreen(self, self.theme)
        self.diagnostics = DiagnosticsScreen(self, self.theme)

        self.screen_manager.add_widget(self.dashboard)
        self.screen_manager.add_widget(self.networks)
        self.screen_manager.add_widget(self.alerts)
        self.screen_manager.add_widget(self.history)
        self.screen_manager.add_widget(self.settings)
        self.screen_manager.add_widget(self.diagnostics)

        root.add_widget(self.screen_manager)

        self.footer_nav = FooterNav(self.theme, self.screen_manager)
        root.add_widget(self.footer_nav)
        return root

    def on_start(self) -> None:
        Clock.schedule_interval(self.process_queue, 0.25)
        Clock.schedule_interval(self.refresh_history, 5.0)
        if self.demo:
            Clock.schedule_interval(self._demo_tick, 1.0)

    def start_monitoring(self) -> None:
        self.header_bar.set_message(None)
        self.state.alerts = []
        self.state.session_alert_count = 0
        self.state.last_alert_time = None
        self.state.last_error = None
        self.interface_choice = "wlan1"
        self.app_config.capture.interface = self.interface_choice
        iface = self.interface_choice
        self.network_filter_mode = "all"
        self.controller.start(interface=iface, network_filter_mode=self.network_filter_mode)

    def set_network_filter_mode(self, mode: str) -> None:
        self.network_filter_mode = "all"
        set_setting("network_filter_mode", "all", db_path=self.db_path)
        self.controller.set_network_filter_mode("all")

    def stop_monitoring(self) -> None:
        self.controller.stop()

    def show_screen(self, name: str) -> None:
        if self.screen_manager:
            self.screen_manager.current = name
        if name == "settings" and self.settings:
            self.settings.refresh()
        if name == "history" and self.history:
            self.history.refresh()

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
        if updated_networks and self.networks:
            self.networks.update_networks(self.state.networks)
        if updated_alerts and self.alerts:
            self.alerts.update_alerts(self.state.alerts)

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
        if self.screen_manager and self.screen_manager.current != "history":
            return
        if self.history:
            self.history.refresh()

    def _demo_tick(self, _dt) -> None:
        self.state.status.update(
            {
                "running": True,
                "adapter_ok": True,
                "monitor_mode": True,
                "logging_on": True,
                "interface": self.interface_choice or "wlan1",
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
