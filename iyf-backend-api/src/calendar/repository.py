"""calendar リポジトリ（Events）。

公開一覧は GSI(status=published, event_date_epoch 昇順) を Query（Scan 回避）。
"""
from __future__ import annotations

from src.calendar.models import Event, EventStatus
from src.common.config import TABLE_EVENTS
from src.common.db import Repository

_GSI_DATE = "GSI-date"
_GSI_PK = "gsi_status"
_GSI_SK = "event_date_epoch"

_GSI_STATUS = "GSI-status"          # 管理系（draft 含む, Phase2）。SK は event_date_epoch。
_GSI_STATUS_PK = "status"


def _strip_none(item: dict) -> dict:
    return {k: v for k, v in item.items() if v is not None}


def event_to_item(event: Event) -> dict:
    item = event.model_dump()
    item["status"] = event.status.value          # GSI-status PK（常時）
    if event.status == EventStatus.PUBLISHED:
        item[_GSI_PK] = "published"
    return _strip_none(item)


def item_to_event(item: dict) -> Event:
    return Event.model_validate(item)


class EventRepository(Repository):
    def __init__(self):
        super().__init__(TABLE_EVENTS)

    def get_event(self, event_id: str) -> Event | None:
        item = self.get({"event_id": event_id})
        return item_to_event(item) if item else None

    def list_published(
        self, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Event], dict | None]:
        # 昇順（近い日付から）で返す。
        items, next_key = self.query_index(
            _GSI_DATE, _GSI_PK, "published",
            limit=limit, ascending=True, start_key=start_key,
        )
        return [item_to_event(i) for i in items], next_key

    # ---- 管理系（Phase2, 共有編集: オーナー制なし） ----

    def save(self, event: Event) -> None:
        self.put(event_to_item(event))

    def delete_event(self, event_id: str) -> None:
        self.delete({"event_id": event_id})

    def list_by_status(
        self, status_value: str, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Event], dict | None]:
        items, next_key = self.query_index(
            _GSI_STATUS, _GSI_STATUS_PK, status_value,
            limit=limit, ascending=True, start_key=start_key,
        )
        return [item_to_event(i) for i in items], next_key
