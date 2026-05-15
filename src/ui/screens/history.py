from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen

from ..components import Card
from ..theme import Theme
from ...storage.db import list_alert_history, list_session_summaries


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_duration(start: Optional[str], end: Optional[str]) -> str:
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


class SessionRow(RecycleDataViewBehavior, BoxLayout):
    session_id = NumericProperty(0)
    summary = StringProperty("")
    selected = BooleanProperty(False)
    theme_ref: Optional[Theme] = None

    def __init__(self, **kwargs) -> None:
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for SessionRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.spacing = theme.gap_s
        self.label = Label(color=theme.palette.text, font_size=theme.body, halign="left")
        self.label.bind(size=lambda *_: setattr(self.label, "text_size", self.label.size))
        self.add_widget(self.label)
        self.on_select = None

    def refresh_view_attrs(self, rv, index, data):
        self.session_id = data.get("session_id", 0)
        self.summary = data.get("summary", "")
        self.label.text = self.summary
        self.on_select = data.get("on_select")
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.on_select:
            self.on_select(self.session_id)
        return True


class HistoryAlertRow(RecycleDataViewBehavior, BoxLayout):
    theme_ref: Optional[Theme] = None

    def __init__(self, **kwargs) -> None:
        theme = self.__class__.theme_ref
        if theme is None:
            raise RuntimeError("Theme not set for HistoryAlertRow")
        super().__init__(orientation="horizontal", size_hint_y=None, height=theme.row_height, **kwargs)
        self.theme = theme
        self.label = Label(color=theme.palette.text, font_size=theme.body, halign="left")
        self.label.bind(size=lambda *_: setattr(self.label, "text_size", self.label.size))
        self.add_widget(self.label)

    def refresh_view_attrs(self, rv, index, data):
        self.label.text = data.get("summary", "")
        return super().refresh_view_attrs(rv, index, data)


class HistoryScreen(Screen):
    def __init__(self, app, theme: Theme, **kwargs) -> None:
        super().__init__(name="history", **kwargs)
        self.app = app
        self.theme = theme
        self.selected_session: Optional[int] = None

        root = BoxLayout(
            orientation="horizontal",
            padding=[theme.gap_m, theme.gap_m, theme.gap_m, theme.gap_m],
            spacing=theme.gap_m,
        )

        self.sessions_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        self.sessions_card.size_hint_x = 0.5
        self.sessions_card.add_widget(Label(text="Sessions", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24)))

        self.sessions_view = RecycleView()
        SessionRow.theme_ref = theme
        self.sessions_view.viewclass = SessionRow
        layout = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout.default_size_hint = (1, None)
        layout.size_hint_y = None
        layout.bind(minimum_height=layout.setter("height"))
        self.sessions_view.add_widget(layout)
        self.sessions_view.layout_manager = layout
        self.sessions_card.add_widget(self.sessions_view)
        root.add_widget(self.sessions_card)

        self.alerts_card = Card(theme, orientation="vertical", padding=theme.gap_m, spacing=theme.gap_s)
        self.alerts_card.size_hint_x = 0.5
        self.alerts_card.add_widget(Label(text="Session Alerts", color=theme.palette.text, font_size=theme.h2, size_hint_y=None, height=theme.dp(24)))

        self.alerts_view = RecycleView()
        HistoryAlertRow.theme_ref = theme
        self.alerts_view.viewclass = HistoryAlertRow
        layout_alerts = RecycleBoxLayout(orientation="vertical", default_size=(None, theme.row_height))
        layout_alerts.default_size_hint = (1, None)
        layout_alerts.size_hint_y = None
        layout_alerts.bind(minimum_height=layout_alerts.setter("height"))
        self.alerts_view.add_widget(layout_alerts)
        self.alerts_view.layout_manager = layout_alerts
        self.alerts_card.add_widget(self.alerts_view)
        root.add_widget(self.alerts_card)

        self.add_widget(root)

    def refresh(self) -> None:
        sessions = list_session_summaries(limit=20, db_path=self.app.db_path)
        rows = []
        for session in sessions:
            duration = _format_duration(session.get("start_time"), session.get("end_time"))
            summary = (
                f"#{session.get('id')} {session.get('interface') or '-'} "
                f"{session.get('start_time')} {duration} alerts={session.get('alert_count')}"
            )
            rows.append(
                {
                    "session_id": session.get("id"),
                    "summary": summary,
                    "on_select": self._select_session,
                }
            )
        if rows:
            self.sessions_view.data = rows
        else:
            self.sessions_view.data = [{"summary": "No sessions", "session_id": 0, "on_select": None}]

        if self.selected_session is None and sessions:
            self.selected_session = sessions[0].get("id")
        self._load_alerts(self.selected_session)

    def _select_session(self, session_id: int) -> None:
        self.selected_session = session_id
        self._load_alerts(session_id)

    def _load_alerts(self, session_id: Optional[int]) -> None:
        if session_id is None:
            self.alerts_view.data = [{"summary": "No alerts"}]
            return
        alerts = list_alert_history(limit=50, session_id=session_id, db_path=self.app.db_path)
        rows = []
        for alert in alerts:
            details = alert.get("details")
            key = details.get("key") if isinstance(details, dict) else None
            summary = f"{alert.get('timestamp')} {alert.get('alert_type')} key={key}"
            rows.append({"summary": summary})
        self.alerts_view.data = rows or [{"summary": "No alerts"}]
