"""calendar モデル・サービス・往復テスト。"""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.calendar.models import Event, EventStatus
from src.calendar.repository import event_to_item, item_to_event
from src.calendar.service import CalendarService
from src.common.errors import NotFoundError


class _FakeEventRepo:
    def __init__(self, events):
        self._by_id = {e.event_id: e for e in events}
        self._published = [e for e in events if e.is_public()]

    def get_event(self, eid):
        return self._by_id.get(eid)

    def list_published(self, *, limit, start_key=None):
        return self._published[:limit], None


def _event(eid, status, epoch):
    return Event(
        event_id=eid, title="練習試合", event_date="2026-07-25T10:00:00+09:00",
        event_date_epoch=epoch, status=status,
    )


def test_get_event_hides_draft():
    svc = CalendarService(_FakeEventRepo([_event("e1", EventStatus.DRAFT, 1)]))
    with pytest.raises(NotFoundError):
        svc.get_event("e1")


def test_list_events_summary():
    svc = CalendarService(_FakeEventRepo([_event("e1", EventStatus.PUBLISHED, 1)]))
    result = svc.list_events()
    assert result["items"][0]["event_id"] == "e1"
    # カレンダー表示のため description を要約に含める（Phase 2 での変更）。
    assert "description" in result["items"][0]


@given(epoch=st.integers(min_value=0, max_value=2_000_000_000), published=st.booleans())
def test_event_item_roundtrip(epoch, published):
    status = EventStatus.PUBLISHED if published else EventStatus.DRAFT
    ev = _event("e", status, epoch)
    restored = item_to_event(event_to_item(ev))
    assert restored.event_id == ev.event_id
    assert restored.event_date_epoch == ev.event_date_epoch
    assert restored.status == ev.status
