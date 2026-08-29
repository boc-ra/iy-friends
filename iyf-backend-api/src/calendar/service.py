"""calendar サービス（公開読み取り US-10 ＋ 管理 US-11）。

管理系は共有編集（BR-OWN-03）: カレンダー権限を持つ Admin/Editor は
任意の Event を作成/編集/削除できる（オーナー制なし）。作成者は監査で追跡。
"""
from __future__ import annotations

import uuid

from src.calendar.models import Event, EventInput, EventStatus, event_admin_summary
from src.calendar.repository import EventRepository
from src.common.audit import record_change
from src.common.auth import Principal
from src.common.config import PAGE_SIZE
from src.common.errors import NotFoundError, UnprocessableError
from src.common.validation import sanitize_text


class CalendarService:
    def __init__(self, event_repo: EventRepository | None = None):
        self._events = event_repo or EventRepository()

    def list_events(self, *, start_key: dict | None = None) -> dict:
        events, next_key = self._events.list_published(limit=PAGE_SIZE, start_key=start_key)
        return {
            "items": [e.to_summary() for e in events],
            "next_cursor": next_key,
        }

    def get_event(self, event_id: str) -> Event:
        event = self._events.get_event(event_id)
        if event is None or not event.is_public():
            raise NotFoundError()
        return event

    # ================= 管理系（Phase 2, US-11） =================

    def create_event(
        self, principal: Principal, data: EventInput, *, event_date_epoch: int, now_iso: str
    ) -> dict:
        self._validate_publish(data.status, data.title, data.event_date)
        event = Event(
            event_id=str(uuid.uuid4()),
            title=sanitize_text(data.title),
            description=sanitize_text(data.description),
            location=data.location,
            event_date=data.event_date,
            event_date_epoch=event_date_epoch,
            status=data.status,
        )
        self._events.save(event)
        record_change(
            entity="Event", entity_id=event.event_id, action="create",
            actor=principal.sub, before=None, after={"status": event.status.value},
        )
        return event.model_dump()

    def update_event(
        self, principal: Principal, event_id: str, data: EventInput,
        *, event_date_epoch: int, now_iso: str,
    ) -> dict:
        event = self._events.get_event(event_id)
        if event is None:
            raise NotFoundError()
        self._validate_publish(data.status, data.title, data.event_date)
        event.title = sanitize_text(data.title)
        event.description = sanitize_text(data.description)
        event.location = data.location
        event.event_date = data.event_date
        event.event_date_epoch = event_date_epoch
        event.status = data.status
        self._events.save(event)
        record_change(
            entity="Event", entity_id=event_id, action="update",
            actor=principal.sub, before=None, after={"status": event.status.value},
        )
        return event.model_dump()

    def delete_event(self, principal: Principal, event_id: str) -> None:
        event = self._events.get_event(event_id)
        if event is None:
            raise NotFoundError()
        self._events.delete_event(event_id)
        record_change(
            entity="Event", entity_id=event_id, action="delete",
            actor=principal.sub, before={"status": event.status.value}, after=None,
        )

    def list_events_admin(
        self, *, status: str | None = None, start_key: dict | None = None
    ) -> dict:
        if status is not None:
            events, next_key = self._events.list_by_status(status, limit=PAGE_SIZE, start_key=start_key)
        else:
            pub, next_key = self._events.list_by_status(
                EventStatus.PUBLISHED.value, limit=PAGE_SIZE, start_key=start_key
            )
            drafts, _ = self._events.list_by_status(EventStatus.DRAFT.value, limit=PAGE_SIZE)
            events = (drafts + pub)[:PAGE_SIZE]
        return {"items": [event_admin_summary(e) for e in events], "next_cursor": next_key}

    def get_event_admin(self, event_id: str) -> dict:
        event = self._events.get_event(event_id)
        if event is None:
            raise NotFoundError()
        return event.model_dump()

    @staticmethod
    def _validate_publish(status, title: str, event_date: str) -> None:
        if status == EventStatus.PUBLISHED:
            if not title.strip() or not event_date.strip():
                raise UnprocessableError("公開にはタイトルと日付が必要です。")
