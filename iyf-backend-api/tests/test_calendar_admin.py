"""calendar 管理系: 共有編集（オーナー制なし）・状態・監査。"""
from __future__ import annotations

import pytest

from src.calendar.models import Event, EventInput, EventStatus
from src.calendar.service import CalendarService
from src.common.auth import ROLE_EDITOR, Principal
from src.common.errors import NotFoundError, UnprocessableError


class _FakeEventRepo:
    def __init__(self, events=None):
        self._by_id = {e.event_id: e for e in (events or [])}
        self.saved = []
        self.deleted = []

    def get_event(self, event_id):
        return self._by_id.get(event_id)

    def save(self, event):
        self._by_id[event.event_id] = event
        self.saved.append(event)

    def delete_event(self, event_id):
        self._by_id.pop(event_id, None)
        self.deleted.append(event_id)

    def list_by_status(self, status_value, *, limit, start_key=None):
        items = [e for e in self._by_id.values() if e.status.value == status_value]
        return items[:limit], None


def _editor(sub="ed1"):
    return Principal(sub=sub, role=ROLE_EDITOR, groups=("editor",))


def _event(eid, status=EventStatus.PUBLISHED):
    return Event(event_id=eid, title="練習", event_date="2026-08-01T10:00:00+09:00",
                 event_date_epoch=1, status=status)


def _input(status=EventStatus.PUBLISHED):
    return EventInput(title="試合", description="市民体育館", location="体育館",
                      event_date="2026-08-10T10:00:00+09:00", status=status)


def test_create_event():
    repo = _FakeEventRepo()
    svc = CalendarService(repo)
    out = svc.create_event(_editor(), _input(), event_date_epoch=123, now_iso="t")
    assert out["status"] == "published"
    assert repo.saved[0].event_date_epoch == 123


def test_create_event_published_requires_title_date():
    svc = CalendarService(_FakeEventRepo())
    with pytest.raises(UnprocessableError):
        # title 空を無理に作るため EventInput を回避し、直接検証を突く。
        svc._validate_publish(EventStatus.PUBLISHED, "   ", "2026-08-01T00:00:00+09:00")


def test_editor_can_edit_any_event_shared():
    # 共有編集: 他人が作った想定の Event も editor が編集可（オーナー制なし）。
    repo = _FakeEventRepo([_event("e1")])
    svc = CalendarService(repo)
    out = svc.update_event(_editor("someone-else"), "e1", _input(), event_date_epoch=200, now_iso="t")
    assert out["title"] == "試合"


def test_delete_event():
    repo = _FakeEventRepo([_event("e1")])
    svc = CalendarService(repo)
    svc.delete_event(_editor(), "e1")
    assert repo.deleted == ["e1"]


def test_update_missing_event_404():
    svc = CalendarService(_FakeEventRepo())
    with pytest.raises(NotFoundError):
        svc.update_event(_editor(), "nope", _input(), event_date_epoch=1, now_iso="t")


def test_list_events_admin_includes_drafts():
    repo = _FakeEventRepo([
        _event("pub", EventStatus.PUBLISHED),
        _event("dft", EventStatus.DRAFT),
    ])
    svc = CalendarService(repo)
    result = svc.list_events_admin()
    ids = {i["event_id"] for i in result["items"]}
    assert ids == {"pub", "dft"}
