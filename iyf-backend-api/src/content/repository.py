"""content リポジトリ（Posts / Notices）。

公開一覧は GSI-published(status=published, published_at_epoch 降順) を Query（Scan 回避）。
管理系一覧は GSI-status(status, updated_at_epoch 降順) を Query（draft 含む, Phase2）。
DynamoDB アイテム ⇔ ドメインモデルの変換を担う（シリアライズ往復は PBT 対象）。
"""
from __future__ import annotations

from src.common.config import TABLE_NOTICES, TABLE_POSTS
from src.common.db import Repository
from src.content.models import Notice, Post, PublishStatus

_GSI_PUBLISHED = "GSI-published"
_GSI_PUB_PK = "gsi_status"          # published のときのみ設定（sparse）
_GSI_PUB_SK = "published_at_epoch"

_GSI_STATUS = "GSI-status"          # 管理系（draft 含む, Phase2）
_GSI_STATUS_PK = "status"           # 常時設定（draft/published）
_GSI_STATUS_SK = "updated_at_epoch"


def _strip_none(item: dict) -> dict:
    """None 属性を除去（DynamoDB の NULL 保存と GSI キー欠落を避ける）。"""
    return {k: v for k, v in item.items() if v is not None}


def post_to_item(post: Post) -> dict:
    item = post.model_dump()
    item["status"] = post.status.value          # GSI-status PK（常時）
    # 公開時のみ sparse GSI-published のパーティションキーを付与。
    if post.status == PublishStatus.PUBLISHED:
        item[_GSI_PUB_PK] = "published"
    return _strip_none(item)


def item_to_post(item: dict) -> Post:
    return Post.model_validate(item)


def notice_to_item(notice: Notice) -> dict:
    item = notice.model_dump()
    item["status"] = notice.status.value
    if notice.status == PublishStatus.PUBLISHED:
        item[_GSI_PUB_PK] = "published"
    return _strip_none(item)


def item_to_notice(item: dict) -> Notice:
    return Notice.model_validate(item)


class PostRepository(Repository):
    def __init__(self):
        super().__init__(TABLE_POSTS)

    def get_post(self, post_id: str) -> Post | None:
        item = self.get({"post_id": post_id})
        return item_to_post(item) if item else None

    def list_published(
        self, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Post], dict | None]:
        items, next_key = self.query_index(
            _GSI_PUBLISHED, _GSI_PUB_PK, "published",
            limit=limit, ascending=False, start_key=start_key,
        )
        return [item_to_post(i) for i in items], next_key

    # ---- 管理系（Phase2） ----

    def save(self, post: Post) -> None:
        self.put(post_to_item(post))

    def delete_post(self, post_id: str) -> None:
        self.delete({"post_id": post_id})

    def list_by_status(
        self, status_value: str, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Post], dict | None]:
        items, next_key = self.query_index(
            _GSI_STATUS, _GSI_STATUS_PK, status_value,
            limit=limit, ascending=False, start_key=start_key,
        )
        return [item_to_post(i) for i in items], next_key


class NoticeRepository(Repository):
    def __init__(self):
        super().__init__(TABLE_NOTICES)

    def get_notice(self, notice_id: str) -> Notice | None:
        item = self.get({"notice_id": notice_id})
        return item_to_notice(item) if item else None

    def list_published(
        self, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Notice], dict | None]:
        items, next_key = self.query_index(
            _GSI_PUBLISHED, _GSI_PUB_PK, "published",
            limit=limit, ascending=False, start_key=start_key,
        )
        return [item_to_notice(i) for i in items], next_key

    # ---- 管理系（Phase2） ----

    def save(self, notice: Notice) -> None:
        self.put(notice_to_item(notice))

    def delete_notice(self, notice_id: str) -> None:
        self.delete({"notice_id": notice_id})

    def list_by_status(
        self, status_value: str, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Notice], dict | None]:
        items, next_key = self.query_index(
            _GSI_STATUS, _GSI_STATUS_PK, status_value,
            limit=limit, ascending=False, start_key=start_key,
        )
        return [item_to_notice(i) for i in items], next_key
