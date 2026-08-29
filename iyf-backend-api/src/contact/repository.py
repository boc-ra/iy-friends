"""contact リポジトリ（Inquiries）。

- 保存（PutItem）。
- 軽量冪等: GSI(dedup_key, created_at_epoch) で短時間ウィンドウ内の重複を検出（Q-D2=A）。
"""
from __future__ import annotations

from src.common.config import TABLE_INQUIRIES
from src.common.db import Repository
from src.contact.models import Inquiry, InquiryStatus

_GSI_DEDUP = "GSI-dedup"
_GSI_PK = "dedup_key"
_GSI_SK = "created_at_epoch"

_GSI_STATUS = "GSI-status"          # 管理系一覧（status, created_at_epoch 降順, Phase2）
_GSI_STATUS_PK = "status"
_GSI_STATUS_SK = "created_at_epoch"


def inquiry_to_item(inquiry: Inquiry) -> dict:
    item = inquiry.model_dump()
    item["status"] = inquiry.status.value
    return item


def item_to_inquiry(item: dict) -> Inquiry:
    return Inquiry.model_validate(item)


class InquiryRepository(Repository):
    def __init__(self):
        super().__init__(TABLE_INQUIRIES)

    def save(self, inquiry: Inquiry) -> None:
        self.put(inquiry_to_item(inquiry))

    def update_notified(self, inquiry_id: str, notified: bool) -> None:
        self._table.update_item(
            Key={"inquiry_id": inquiry_id},
            UpdateExpression="SET notified = :n",
            ExpressionAttributeValues={":n": notified},
        )

    def find_recent_duplicate(self, dedup_key: str, since_epoch: int) -> bool:
        """短時間ウィンドウ内に同一 dedup_key が存在するか（軽量冪等）。"""
        items = self.query_recent_by(
            _GSI_DEDUP, _GSI_PK, dedup_key,
            since_epoch=since_epoch, range_key=_GSI_SK,
        )
        return len(items) > 0

    # ---- 管理系（Phase2, Admin のみ） ----

    def get_inquiry(self, inquiry_id: str) -> Inquiry | None:
        item = self.get({"inquiry_id": inquiry_id})
        return item_to_inquiry(item) if item else None

    def list_by_status(
        self, status_value: str, *, limit: int, start_key: dict | None = None
    ) -> tuple[list[Inquiry], dict | None]:
        items, next_key = self.query_index(
            _GSI_STATUS, _GSI_STATUS_PK, status_value,
            limit=limit, ascending=False, start_key=start_key,
        )
        return [item_to_inquiry(i) for i in items], next_key

    def update_status(self, inquiry_id: str, status_value: str, updated_by: str, updated_at: str) -> None:
        self.update_item(
            {"inquiry_id": inquiry_id},
            {"status": status_value, "updated_by": updated_by, "updated_at": updated_at},
        )
