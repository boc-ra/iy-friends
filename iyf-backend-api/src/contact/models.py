"""contact ドメインモデル（Inquiry）。

- フィールド: name / email / message（すべて必須, Q-F3=A）。PII。
- status: 未対応 / 対応中 / 対応済（Q-F2=B）。受付時は「未対応」。
- notified: SES 通知の成否（ベストエフォート, Q-D1=A）。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class InquiryStatus(str, Enum):
    NEW = "未対応"
    IN_PROGRESS = "対応中"
    DONE = "対応済"


class InquiryCreate(BaseModel):
    """問い合わせ送信リクエスト（入力検証, SECURITY-05）。"""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5_000)


class Inquiry(BaseModel):
    """永続化される問い合わせ。"""

    inquiry_id: str
    name: str
    email: str
    message: str
    status: InquiryStatus = InquiryStatus.NEW
    created_at: str                # ISO8601(JST)
    created_at_epoch: int          # GSI ソート/冪等ウィンドウ用
    dedup_key: str                 # email+message のハッシュ（軽量冪等, Q-D2=A）
    notified: bool = False         # SES 通知成否
    updated_at: str | None = None  # 状態更新日時（Phase2）
    updated_by: str | None = None  # 最終更新者(sub)（Phase2）

    def to_summary(self) -> dict:
        """管理一覧用（本文は含めるが一覧では短め運用可）。"""
        return {
            "inquiry_id": self.inquiry_id,
            "name": self.name,
            "email": self.email,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class InquiryStatusUpdate(BaseModel):
    """問い合わせ対応状況の更新（管理系, Phase2）。"""

    status: InquiryStatus
