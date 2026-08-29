"""calendar ドメインモデル（Event）。

- 活動予定。日付順（昇順）で公開一覧を返す。
- 日時は JST・ISO8601。GSI ソート用に event_date_epoch を保持。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Event(BaseModel):
    event_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20_000)
    location: str | None = Field(default=None, max_length=200)
    event_date: str                      # ISO8601(JST) 表示用
    event_date_epoch: int                # GSI ソート用
    status: EventStatus = EventStatus.DRAFT

    def is_public(self) -> bool:
        return self.status == EventStatus.PUBLISHED

    def to_summary(self) -> dict:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "event_date": self.event_date,
        }


class EventInput(BaseModel):
    """イベント作成/更新の入力（管理系, Phase2）。

    既存 Event の実装フィールドに合わせる（title/description/location/event_date/status）。
    event_date は ISO8601(JST) 文字列。epoch はサービス層で算出。
    """

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20_000)
    location: str | None = Field(default=None, max_length=200)
    event_date: str = Field(min_length=1)
    status: EventStatus = EventStatus.DRAFT


def event_admin_summary(event: Event) -> dict:
    base = event.to_summary()
    base["status"] = event.status.value
    return base
