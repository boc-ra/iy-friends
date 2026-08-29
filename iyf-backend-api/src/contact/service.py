"""contact サービス（問い合わせ受付, US-13）。

フロー（Q-D1=A / Q-D2=A / NFR-U3-REL-01）:
  1. 入力検証（SECURITY-05, models.InquiryCreate）
  2. 軽量冪等チェック（同一 email+message の短時間重複を無視）
  3. DynamoDB 保存（未対応）  ← ここまで成立で受付完了（fail-closed: 失敗は 5xx）
  4. SES 同期通知（ベストエフォート。失敗は notified=False、受付は成立）
  5. 受付ID を返す
"""
from __future__ import annotations

import hashlib
import uuid

from src.common.audit import record_change
from src.common.auth import Principal
from src.common.config import CONTACT_DEDUP_WINDOW_SECONDS, PAGE_SIZE
from src.common.errors import NotFoundError
from src.common.validation import sanitize_text
from src.contact.models import Inquiry, InquiryCreate, InquiryStatus
from src.contact.notifier import notify_new_inquiry
from src.contact.repository import InquiryRepository


def compute_dedup_key(email: str, message: str) -> str:
    """email+message から冪等キーを生成する純粋関数（PBT 対象）。"""
    normalized = f"{email.strip().lower()}|{message.strip()}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ContactService:
    def __init__(
        self,
        repo: InquiryRepository | None = None,
        *,
        clock_epoch: int | None = None,
        now_iso: str | None = None,
    ):
        self._repo = repo or InquiryRepository()
        # 時刻はハンドラ層から注入（テスト容易性・決定性）。
        self._clock_epoch = clock_epoch
        self._now_iso = now_iso

    def submit(self, payload: InquiryCreate, *, created_at_epoch: int, created_at_iso: str) -> dict:
        dedup_key = compute_dedup_key(payload.email, payload.message)

        # 2. 軽量冪等: 短時間ウィンドウ内の重複は成功扱いで無視（新規保存しない）。
        since = created_at_epoch - CONTACT_DEDUP_WINDOW_SECONDS
        if self._repo.find_recent_duplicate(dedup_key, since):
            return {"status": "accepted", "duplicate": True}

        inquiry = Inquiry(
            inquiry_id=str(uuid.uuid4()),
            name=sanitize_text(payload.name),
            email=payload.email,
            message=sanitize_text(payload.message),
            status=InquiryStatus.NEW,
            created_at=created_at_iso,
            created_at_epoch=created_at_epoch,
            dedup_key=dedup_key,
            notified=False,
        )

        # 3. 保存（失敗時は例外→グローバルハンドラで 5xx, fail-closed）。
        self._repo.save(inquiry)
        record_change(
            entity="Inquiry", entity_id=inquiry.inquiry_id,
            action="create", actor="public", before=None, after={"status": inquiry.status.value},
        )

        # 4. SES ベストエフォート通知。
        notified = notify_new_inquiry(inquiry.inquiry_id, inquiry.name)
        if notified:
            try:
                self._repo.update_notified(inquiry.inquiry_id, True)
            except Exception:  # noqa: BLE001 — 通知フラグ更新失敗は受付成立に影響させない。
                pass

        return {"status": "accepted", "inquiry_id": inquiry.inquiry_id, "duplicate": False}

    # ================= 管理系（Phase 2, US-14 / Admin のみ） =================

    def list_inquiries(self, *, status: str | None = None, start_key: dict | None = None) -> dict:
        if status is not None:
            items, next_key = self._repo.list_by_status(status, limit=PAGE_SIZE, start_key=start_key)
        else:
            # status 指定なし: 全ステータスを結合し受信日時降順（小規模前提）。
            merged: list[Inquiry] = []
            for st in (InquiryStatus.NEW, InquiryStatus.IN_PROGRESS, InquiryStatus.DONE):
                part, _ = self._repo.list_by_status(st.value, limit=PAGE_SIZE)
                merged.extend(part)
            merged.sort(key=lambda i: i.created_at_epoch, reverse=True)
            items, next_key = merged[:PAGE_SIZE], None
        return {"items": [i.to_summary() for i in items], "next_cursor": next_key}

    def get_inquiry(self, inquiry_id: str) -> dict:
        inquiry = self._repo.get_inquiry(inquiry_id)
        if inquiry is None:
            raise NotFoundError()
        return inquiry.model_dump()

    def update_inquiry_status(
        self, actor: Principal, inquiry_id: str, status: InquiryStatus, *, now_iso: str
    ) -> dict:
        inquiry = self._repo.get_inquiry(inquiry_id)
        if inquiry is None:
            raise NotFoundError()
        before = inquiry.status.value
        self._repo.update_status(inquiry_id, status.value, actor.sub, now_iso)
        record_change(
            entity="Inquiry", entity_id=inquiry_id, action=f"set_status:{status.value}",
            actor=actor.sub, before={"status": before}, after={"status": status.value},
        )
        updated = self._repo.get_inquiry(inquiry_id)
        return updated.model_dump() if updated else {}
