"""Alerts screen with live and historical views."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from ...storage.db import list_alert_history, list_session_summaries
from ..components import Card
from ..theme import Theme


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp string into a datetime."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_duration(start: Optional[str], end: Optional[str]) -> str:
    """Format a duration between two ISO timestamps."""
    start_dt = _parse_iso(start)
    end_dt = _parse_iso(end)
    if not start_dt or not end_dt:
        return "-"
    delta = end_dt - start_dt
    total = int(delta.total_seconds())
    minutes, seconds = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


class AlertRow(RecycleDataViewBehavior, BoxLayout):
    """Recycler row for a live alert — horizontal label:value format."""

    theme_ref: Theme = None

    def __init__(self, **kwargs) -> None:
        """Create a horizontal alert row with inline labels."""
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for AlertRow")
        super().__init__(orientation="vertical", size_hint_y=None, height=theme.dp(48), **kwargs)
        self.theme = theme
        self.padding = [theme.gap_s, theme.gap_xs, theme.gap_s, theme.gap_xs]
        self.spacing = theme.gap_xs
        self.alert_data: Dict[str, object] = {}

        # Top line: timestamp + type
        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.dp(18), spacing=theme.gap_s)
        self.label_ts = Label(
            color=theme.palette.text_dim, font_size=theme.caption,
            size_hint_x=None, width=theme.dp(110), halign="left", valign="middle",
        )
        self.label_type = Label(
            color=theme.palette.accent, font_size=theme.caption,
            size_hint_x=None, width=theme.dp(100), halign="left", valign="middle",
        )
        top.add_widget(self.label_ts)
        top.add_widget(self.label_type)
        top.add_widget(Label(size_hint_x=1))  # spacer
        self.add_widget(top)

        # Bottom line: BSSID + PCAP
        bot = BoxLayout(orientation="horizontal", size_hint_y=None, height=theme.dp(18), spacing=theme.gap_s)
        self.label_key = Label(
            color=theme.palette.text, font_size=theme.caption,
            halign="left", valign="middle",
        )
        self.label_pcap = Label(
            color=theme.palette.text_dim, font_size=theme.caption,
            size_hint_x=None, width=theme.dp(80), halign="right", valign="middle",
        )
        bot.add_widget(self.label_key)
        bot.add_widget(self.label_pcap)
        self.add_widget(bot)

    def refresh_view_attrs(self, rv, index, data):
        """Bind row properties from recycler data."""
        self.alert_data = data.get("alert_data", {})
        self.label_ts.text = data.get("timestamp", "")
        self.label_type.text = data.get("alert_type", "")
        self.label_key.text = data.get("summary", "")
        self.label_pcap.text = data.get("pcap", "")
        for lbl in (self.label_ts, self.label_type, self.label_key, self.label_pcap):
            lbl.text_size = (lbl.width, None)
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Open a details popup when the row is tapped."""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._show_details()
        return True

    def _show_details(self) -> None:
        """Show a popup with alert details."""
        details = self.alert_data
        message = [
            f"Time: {details.get('timestamp')}",
            f"Type: {details.get('alert_type')}",
            f"Key: {details.get('key')}",
            f"Count: {details.get('count')}",
        ]
        if details.get("src"):
            message.append(f"Source: {details.get('src')}")
        if details.get("dst"):
            message.append(f"Target: {details.get('dst')}")
        if details.get("bssid"):
            message.append(f"BSSID: {details.get('bssid')}")
        if details.get("reason_code") is not None:
            message.append(f"Reason: {details.get('reason_code')}")
        if details.get("pcap_path"):
            message.append(f"PCAP: {details.get('pcap_path')}")
        content = Label(text="\n".join(message), color=self.theme.palette.text)
        popup = Popup(title="Alert Details", content=content, size_hint=(0.8, 0.6))
        popup.open()


class SessionRow(RecycleDataViewBehavior, BoxLayout):
    """Recycler row for a stored session."""

    session_id = NumericProperty(0)
    summary = StringProperty("")
    theme_ref: Optional[Theme] = None

    def __init__(self, **kwargs) -> None:
        """Create the row and label."""
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for SessionRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.label = Label(color=theme.palette.text, font_size=theme.body, halign="left")
        self.label.bind(size=lambda *_: setattr(self.label, "text_size", self.label.size))
        self.add_widget(self.label)
        self.on_select = None

    def refresh_view_attrs(self, rv, index, data):
        """Bind row properties from recycler data."""
        self.session_id = data.get("session_id", 0)
        self.summary = data.get("summary", "")
        self.label.text = self.summary
        self.on_select = data.get("on_select")
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Select the session when the row is tapped."""
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.on_select:
            self.on_select(self.session_id)
        return True


class HistoryAlertRow(RecycleDataViewBehavior, BoxLayout):
    """Recycler row for a historical alert."""

    theme_ref: Optional[Theme] = None

    def __init__(self, **kwargs) -> None:
        """Create the row and label."""
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for HistoryAlertRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.label = Label(color=theme.palette.text, font_size=theme.body, halign="left")
        self.label.bind(size=lambda *_: setattr(self.label, "text_size", self.label.size))
        self.add_widget(self.label)

    def refresh_view_attrs(self, rv, index, data):
        """Bind row properties from recycler data."""
        self.label.text = data.get("summary", "")
        return super().refresh_view_attrs(rv, index, data)


def _build_recycler(viewclass, theme: Theme, row_height: Optional[int] = None) -> RecycleView:
    """Build a simple vertical recycler view."""
    rh = row_height if row_height is not None else theme.row_height
    recycler = RecycleView()
    layout = RecycleBoxLayout(orientation="vertical", default_size=(None, rh))
    layout.default_size_hint = (1, None)
    layout.size_hint_y = None
    layout.bind(minimum_height=layout.setter("height"))
    recycler.add_widget(layout)
    recycler.layout_manager = layout
    recycler.viewclass = viewclass
    return recycler


class AlertsScreen(Screen):
    """Alerts screen with live feed and stored sessions."""

    def __init__(self, app, theme: Theme, **kwargs) -> None:
        """Build the alerts layout."""
        super().__init__(name="alerts", **kwargs)
        self.app = app
        self.theme = theme
        self.selected_session: Optional[int] = None

        root = BoxLayout(
            orientation="horizontal",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )

        live_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        live_card.size_hint_x = 0.5
        live_card.add_widget(Label(text="Live alerts", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24)))
        live_card.add_widget(Label(text="Tap an alert for details.", color=theme.palette.text_dim, font_size=theme.caption, size_hint_y=None, height=theme.dp(18)))

        AlertRow.theme_ref = theme
        self.live_view = _build_recycler(AlertRow, theme, row_height=theme.dp(48))
        live_card.add_widget(self.live_view)
        root.add_widget(live_card)

        history_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        history_card.size_hint_x = 0.5
        history_card.add_widget(Label(text="Alert history", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24)))
        history_card.add_widget(Label(text="Sessions stored on this device.", color=theme.palette.text_dim, font_size=theme.caption, size_hint_y=None, height=theme.dp(18)))

        history_card.add_widget(Label(text="Sessions", color=theme.palette.text_dim, font_size=theme.caption, size_hint_y=None, height=theme.dp(18)))
        SessionRow.theme_ref = theme
        self.sessions_view = _build_recycler(SessionRow, theme)
        self.sessions_view.size_hint_y = 0.45
        history_card.add_widget(self.sessions_view)

        history_card.add_widget(Label(text="Session Alerts", color=theme.palette.text_dim, font_size=theme.caption, size_hint_y=None, height=theme.dp(18)))
        HistoryAlertRow.theme_ref = theme
        self.history_alerts_view = _build_recycler(HistoryAlertRow, theme)
        self.history_alerts_view.size_hint_y = 0.55
        history_card.add_widget(self.history_alerts_view)
        root.add_widget(history_card)

        self.add_widget(root)

    def update_alerts(self, alerts: List[Dict[str, object]]) -> None:
        """Update the live alert list."""
        rows = []
        for alert in alerts:
            ts_raw = alert.get("timestamp", "")
            # Trim ISO timestamp to a shorter readable form: "15 14:30:00" or "Jan15 14:30"
            ts_short = ts_raw
            if len(ts_raw) > 12:
                try:
                    dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    ts_short = dt.strftime("%m/%d %H:%M:%S")
                except (ValueError, TypeError):
                    ts_short = ts_raw[-8:] if len(ts_raw) >= 8 else ts_raw
            key = alert.get("key") or "-"
            summary = key if len(key) <= 20 else f"{key[:8]}..{key[-6:]}"
            pcap_path = alert.get("pcap_path")
            pcap = Path(pcap_path).name if pcap_path else "-"
            rows.append(
                {
                    "timestamp": ts_short,
                    "alert_type": alert.get("alert_type", ""),
                    "summary": summary,
                    "pcap": pcap,
                    "alert_data": alert,
                }
            )
        self.live_view.data = rows or [{"timestamp": "", "alert_type": "", "summary": "No alerts", "pcap": "", "alert_data": {}}]

    def refresh_history(self) -> None:
        """Reload session list and history panel."""
        sessions = list_session_summaries(limit=20, db_path=self.app.db_path)
        rows = []
        for session in sessions:
            duration = _format_duration(session.get("start_time"), session.get("end_time"))
            session_pcap = session.get("pcap_path")
            session_pcap_name = Path(session_pcap).name if session_pcap else "-"
            summary = (
                f"#{session.get('id')} {session.get('interface') or '-'} "
                f"{session.get('start_time')} {duration} alerts={session.get('alert_count')} "
                f"pcap={session_pcap_name}"
            )
            rows.append(
                {
                    "session_id": session.get("id"),
                    "summary": summary,
                    "on_select": self._select_session,
                }
            )
        self.sessions_view.data = rows or [{"summary": "No sessions", "session_id": 0, "on_select": None}]
        if self.selected_session is None and sessions:
            self.selected_session = sessions[0].get("id")
        self._load_alerts(self.selected_session)

    def _select_session(self, session_id: int) -> None:
        """Select a session and load its alerts."""
        self.selected_session = session_id
        self._load_alerts(session_id)

    def _load_alerts(self, session_id: Optional[int]) -> None:
        """Load and render alerts for the given session."""
        if session_id is None:
            self.history_alerts_view.data = [{"summary": "No alerts"}]
            return
        alerts = list_alert_history(limit=50, session_id=session_id, db_path=self.app.db_path)
        rows = []
        for alert in alerts:
            details = alert.get("details")
            key = details.get("key") if isinstance(details, dict) else None
            count = details.get("count") if isinstance(details, dict) else None
            pcap_path = alert.get("pcap_path")
            pcap = Path(pcap_path).name if pcap_path else "-"
            count_text = str(count) if count is not None else "-"
            summary = f"{alert.get('timestamp')} {alert.get('alert_type')} key={key} count={count_text} pcap={pcap}"
            rows.append({"summary": summary})
        self.history_alerts_view.data = rows or [{"summary": "No alerts"}]
