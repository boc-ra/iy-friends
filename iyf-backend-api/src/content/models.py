"""content ドメインモデル（Post, Notice）。

- status: draft / published（Q-F5=A: 予約公開・失効なし）。
- 公開 API は published のみ返す（BR-STATE）。
- 著者は表示名（ニックネーム可, Q-F1=A）。
- 日時は JST・ISO8601 文字列。GSI 用に epoch 秒も保持。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PublishStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Post(BaseModel):
    """ブログ記事。"""

    post_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=100_000)
    author_display_name: str = Field(min_length=1, max_length=60)
    author_id: str | None = None             # 作成者(Cognito sub)。オーナー認可(IDOR)用。Phase2追加(任意)
    category: str | None = Field(default=None, max_length=60)
    status: PublishStatus = PublishStatus.DRAFT
    published_at: str | None = None          # ISO8601(JST) 表示用
    published_at_epoch: int | None = None    # GSI ソート用
    created_at: str | None = None            # ISO8601(JST) 監査用（Phase2追加）
    updated_at: str | None = None            # ISO8601(JST) 監査用（Phase2追加）
    updated_at_epoch: int | None = None      # GSI-status ソート用（Phase2追加）
    source: str = "native"                   # native / migrated(U4)
    source_url: str | None = None            # 移行元記事URL（U4: 冪等・トレーサビリティ用）

    def is_public(self) -> bool:
        return self.status == PublishStatus.PUBLISHED

    def to_summary(self) -> dict:
        """一覧用の要約（本文を含めない, ペイロード最小化）。"""
        return {
            "post_id": self.post_id,
            "title": self.title,
            "author_display_name": self.author_display_name,
            "category": self.category,
            "published_at": self.published_at,
        }


class Notice(BaseModel):
    """お知らせ。"""

    notice_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=50_000)
    author_display_name: str | None = None   # Phase2追加（任意）
    author_id: str | None = None             # 作成者(Cognito sub)。オーナー認可用（Phase2追加）
    status: PublishStatus = PublishStatus.DRAFT
    published_at: str | None = None
    published_at_epoch: int | None = None
    created_at: str | None = None            # Phase2追加
    updated_at: str | None = None            # Phase2追加
    updated_at_epoch: int | None = None      # GSI-status 用（Phase2追加）

    def is_public(self) -> bool:
        return self.status == PublishStatus.PUBLISHED

    def to_summary(self) -> dict:
        return {
            "notice_id": self.notice_id,
            "title": self.title,
            "published_at": self.published_at,
        }


# ---- 管理入力 DTO（SECURITY-05。body はサービス層でサニタイズ） ----

class PostInput(BaseModel):
    """ブログ作成/更新の入力。"""

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=100_000)
    category: str | None = Field(default=None, max_length=60)
    status: PublishStatus = PublishStatus.DRAFT


class NoticeInput(BaseModel):
    """お知らせ作成/更新の入力。"""

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(max_length=50_000)
    status: PublishStatus = PublishStatus.DRAFT


class StatusUpdate(BaseModel):
    """公開/非公開の切替入力。"""

    status: PublishStatus


def admin_summary(item) -> dict:
    """管理一覧用の要約（status/更新日時を含む。本文は除外）。"""
    base = item.to_summary()
    base["status"] = item.status.value
    base["updated_at"] = getattr(item, "updated_at", None)
    base["author_id"] = getattr(item, "author_id", None)
    return base
