from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from ..config import Config, load_config
from ..orchestration.session_manager import SessionManager
from ..storage.db import (
    get_setting,
    init_db,
    list_alert_history,
    list_sessions,
    set_setting,
)
from ..utils.logging import setup_logging


@dataclass
class UIState:
    status: Dict[str, Any] = field(default_factory=dict)
    networks: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)


class MonitorController:
    def __init__(self, config: Config, event_queue: queue.Queue) -> None:
        self.config = config
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None
        self.session: Optional[SessionManager] = None
        self._lock = threading.Lock()

    def start(self, interface: Optional[str] = None) -> None:
        with self._lock:
            if self.thread and self.thread.is_alive():
                return
            self.session = SessionManager(self.config, event_queue=self.event_queue)
            self.thread = threading.Thread(
                target=self._run,
                args=(interface,),
                daemon=True,
            )
            self.thread.start()

    def _run(self, interface: Optional[str]) -> None:
        if self.session is None:
            return
        exit_code = self.session.run(
            interface=interface,
            install_signal_handlers=False,
            render_console=False,
        )
        self.event_queue.put({"type": "stopped", "data": {"code": exit_code}})

    def stop(self) -> None:
        with self._lock:
            if self.session:
                self.session.stop()
            if self.thread:
                self.thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())


class NavBar(BoxLayout):
    def __init__(self, manager: ScreenManager, **kwargs) -> None:
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(48), **kwargs)
        self.manager = manager
        for name, label in (
            ("home", "Home"),
            ("networks", "Networks"),
            ("alerts", "Alerts"),
            ("history", "History"),
        ):
            button = Button(text=label, font_size=sp(16))
            button.bind(on_press=self._navigate(name))
            self.add_widget(button)

    def _navigate(self, name: str):
        def _handler(_instance):
            self.manager.current = name

        return _handler


class HomeScreen(Screen):
    def __init__(self, app: "PWDBoxApp", **kwargs) -> None:
        super().__init__(name="home", **kwargs)
        self.app = app

        root = BoxLayout(orientation="horizontal", padding=dp(10), spacing=dp(8))

        left = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_x=0.48)
        right = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_x=0.52)

        header = Label(
            text="PWD-Box Status",
            size_hint_y=None,
            height=dp(30),
            font_size=sp(20),
        )
        left.add_widget(header)

        interface_row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        interface_row.add_widget(Label(text="Interface", size_hint_x=0.35, font_size=sp(16)))
        self.interface_input = TextInput(
            text=app.default_interface,
            multiline=False,
            font_size=sp(16),
        )
        interface_row.add_widget(self.interface_input)
        left.add_widget(interface_row)

        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.start_button = Button(text="Start", font_size=sp(16))
        self.stop_button = Button(text="Stop", font_size=sp(16))
        self.start_button.bind(on_press=self._start)
        self.stop_button.bind(on_press=self._stop)
        controls.add_widget(self.start_button)
        controls.add_widget(self.stop_button)
        left.add_widget(controls)

        status_row = BoxLayout(size_hint_y=None, height=dp(24))
        self.status_label = Label(text="Status: idle", font_size=sp(16))
        status_row.add_widget(self.status_label)
        left.add_widget(status_row)

        indicators = GridLayout(cols=1, size_hint_y=None, height=dp(72))
        self.adapter_label = Label(text="Adapter: unknown", font_size=sp(14))
        self.monitor_label = Label(text="Monitor mode: unknown", font_size=sp(14))
        self.logging_label = Label(text="DB logging: unknown", font_size=sp(14))
        indicators.add_widget(self.adapter_label)
        indicators.add_widget(self.monitor_label)
        indicators.add_widget(self.logging_label)
        left.add_widget(indicators)

        self.alert_banner = Label(
            text="No active alerts",
            size_hint_y=None,
            height=dp(32),
            color=(1, 1, 1, 1),
            font_size=sp(16),
        )
        right.add_widget(self.alert_banner)

        right.add_widget(
            Label(
                text="Recent Alerts",
                size_hint_y=None,
                height=dp(24),
                font_size=sp(16),
            )
        )
        self.alerts_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.alerts_grid.bind(minimum_height=self.alerts_grid.setter("height"))
        alerts_scroll = ScrollView()
        alerts_scroll.add_widget(self.alerts_grid)
        right.add_widget(alerts_scroll)

        root.add_widget(left)
        root.add_widget(right)

        self.add_widget(root)

    def _start(self, _instance) -> None:
        iface = self.interface_input.text.strip()
        if iface:
            set_setting("last_interface", iface, self.app.db_path)
        self.app.controller.start(interface=iface or None)

    def _stop(self, _instance) -> None:
        self.app.controller.stop()

    def update_status(self, status: Dict[str, Any], running: bool) -> None:
        self.status_label.text = "Status: running" if running else "Status: idle"
        adapter = "ok" if status.get("adapter_ok") else "off"
        monitor = "on" if status.get("monitor_mode") else "off"
        logging = "on" if status.get("logging_on") else "off"
        self.adapter_label.text = f"Adapter: {adapter}"
        self.monitor_label.text = f"Monitor mode: {monitor}"
        self.logging_label.text = f"DB logging: {logging}"

    def update_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        self.alerts_grid.clear_widgets()
        if not alerts:
            self.alerts_grid.add_widget(Label(text="No alerts", font_size=sp(14)))
            self.alert_banner.text = "No active alerts"
            self.alert_banner.color = (1, 1, 1, 1)
            return

        latest = alerts[0]
        summary = f"ALERT {latest.get('alert_type')} count={latest.get('count')}"
        self.alert_banner.text = summary
        self.alert_banner.color = (1, 0.3, 0.3, 1)
        for alert in alerts[:8]:
            timestamp = alert.get("timestamp")
            key = alert.get("key")
            count = alert.get("count")
            text = f"{timestamp} {alert.get('alert_type')} {key} count={count}"
            self.alerts_grid.add_widget(
                Label(text=text, size_hint_y=None, height=dp(20), font_size=sp(14))
            )


class NetworksScreen(Screen):
    def __init__(self, app: "PWDBoxApp", **kwargs) -> None:
        super().__init__(name="networks", **kwargs)
        self.app = app

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        root.add_widget(
            Label(
                text="Observed Networks",
                size_hint_y=None,
                height=dp(30),
                font_size=sp(20),
            )
        )

        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.grid)
        root.add_widget(scroll)
        self.add_widget(root)

    def update_networks(self, networks: List[Dict[str, Any]]) -> None:
        self.grid.clear_widgets()
        if not networks:
            self.grid.add_widget(Label(text="No networks yet", font_size=sp(14)))
            return
        for item in networks:
            ssid = item.get("ssid") or "<hidden>"
            bssid = item.get("bssid") or "unknown"
            rssi = item.get("rssi") if item.get("rssi") is not None else "-"
            age = item.get("age_seconds", 0)
            text = f"{ssid}  {bssid}  rssi={rssi}  age={age}s"
            self.grid.add_widget(
                Label(text=text, size_hint_y=None, height=dp(20), font_size=sp(14))
            )


class AlertsScreen(Screen):
    def __init__(self, app: "PWDBoxApp", **kwargs) -> None:
        super().__init__(name="alerts", **kwargs)
        self.app = app

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        root.add_widget(
            Label(
                text="Recent Alerts",
                size_hint_y=None,
                height=dp(30),
                font_size=sp(20),
            )
        )

        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.grid)
        root.add_widget(scroll)
        self.add_widget(root)

    def update_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        self.grid.clear_widgets()
        if not alerts:
            self.grid.add_widget(Label(text="No alerts", font_size=sp(14)))
            return
        for alert in alerts:
            text = (
                f"{alert.get('timestamp')} {alert.get('alert_type')} "
                f"key={alert.get('key')} count={alert.get('count')}"
            )
            self.grid.add_widget(
                Label(text=text, size_hint_y=None, height=dp(20), font_size=sp(14))
            )


class HistoryScreen(Screen):
    def __init__(self, app: "PWDBoxApp", **kwargs) -> None:
        super().__init__(name="history", **kwargs)
        self.app = app

        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        root.add_widget(
            Label(text="History", size_hint_y=None, height=dp(30), font_size=sp(20))
        )

        root.add_widget(
            Label(
                text="Recent Sessions",
                size_hint_y=None,
                height=dp(22),
                font_size=sp(16),
            )
        )
        self.sessions_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.sessions_grid.bind(minimum_height=self.sessions_grid.setter("height"))
        sessions_scroll = ScrollView(size_hint_y=0.4)
        sessions_scroll.add_widget(self.sessions_grid)
        root.add_widget(sessions_scroll)

        root.add_widget(
            Label(
                text="Recent Alerts",
                size_hint_y=None,
                height=dp(22),
                font_size=sp(16),
            )
        )
        self.alerts_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4))
        self.alerts_grid.bind(minimum_height=self.alerts_grid.setter("height"))
        alerts_scroll = ScrollView()
        alerts_scroll.add_widget(self.alerts_grid)
        root.add_widget(alerts_scroll)

        self.add_widget(root)

    def refresh(self) -> None:
        sessions = list_sessions(limit=8, db_path=self.app.db_path)
        alerts = list_alert_history(limit=8, db_path=self.app.db_path)

        self.sessions_grid.clear_widgets()
        if not sessions:
            self.sessions_grid.add_widget(Label(text="No sessions", font_size=sp(14)))
        else:
            for session in sessions:
                text = (
                    f"#{session.get('id')} {session.get('interface')} "
                    f"{session.get('start_time')} {session.get('status')}"
                )
                self.sessions_grid.add_widget(
                    Label(text=text, size_hint_y=None, height=dp(20), font_size=sp(14))
                )

        self.alerts_grid.clear_widgets()
        if not alerts:
            self.alerts_grid.add_widget(Label(text="No alerts", font_size=sp(14)))
        else:
            for alert in alerts:
                details = alert.get("details")
                key = details.get("key") if isinstance(details, dict) else None
                text = (
                    f"{alert.get('timestamp')} {alert.get('alert_type')} "
                    f"key={key}"
                )
                self.alerts_grid.add_widget(
                    Label(text=text, size_hint_y=None, height=dp(20), font_size=sp(14))
                )


class PWDBoxApp(App):
    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.state = UIState()
        self.event_queue: queue.Queue = queue.Queue()
        self.controller = MonitorController(config, self.event_queue)
        self.db_path = str(init_db(config.storage.db_path))
        self.default_interface = get_setting(
            "last_interface",
            config.capture.interface or "",
            db_path=self.db_path,
        )
        self.screen_manager: Optional[ScreenManager] = None
        self.home_screen: Optional[HomeScreen] = None
        self.networks_screen: Optional[NetworksScreen] = None
        self.alerts_screen: Optional[AlertsScreen] = None
        self.history_screen: Optional[HistoryScreen] = None

    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.1, 1)
        root = BoxLayout(orientation="vertical")

        manager = ScreenManager()
        self.screen_manager = manager

        self.home_screen = HomeScreen(self)
        self.networks_screen = NetworksScreen(self)
        self.alerts_screen = AlertsScreen(self)
        self.history_screen = HistoryScreen(self)

        manager.add_widget(self.home_screen)
        manager.add_widget(self.networks_screen)
        manager.add_widget(self.alerts_screen)
        manager.add_widget(self.history_screen)

        root.add_widget(NavBar(manager))
        root.add_widget(manager)
        return root

    def on_start(self) -> None:
        Clock.schedule_interval(self.process_queue, 0.5)
        Clock.schedule_interval(self.refresh_history, 5.0)

    def process_queue(self, _dt) -> None:
        updated_alerts = False
        updated_networks = False
        while True:
            try:
                event = self.event_queue.get_nowait()
            except queue.Empty:
                break

            event_type = event.get("type")
            data = event.get("data", {})
            if event_type == "status":
                self.state.status = data
            elif event_type == "networks":
                self.state.networks = data.get("items", [])
                updated_networks = True
            elif event_type == "alert":
                self.state.alerts.insert(0, data)
                self.state.alerts = self.state.alerts[:20]
                updated_alerts = True
            elif event_type == "stopped":
                self.state.status["running"] = False

        if self.home_screen:
            self.home_screen.update_status(self.state.status, self.controller.is_running())
        if updated_networks and self.networks_screen:
            self.networks_screen.update_networks(self.state.networks)
        if updated_alerts:
            if self.alerts_screen:
                self.alerts_screen.update_alerts(self.state.alerts)
            if self.home_screen:
                self.home_screen.update_alerts(self.state.alerts)

    def refresh_history(self, _dt) -> None:
        if self.screen_manager and self.screen_manager.current != "history":
            return
        if self.history_screen:
            self.history_screen.refresh()


def run_ui(config_path: Optional[str] = None) -> int:
    config = load_config(config_path)
    setup_logging(config.logging.level)
    app = PWDBoxApp(config)
    app.run()
    return 0
