"""contact サービス・冪等・往復テスト。SES/DB はフェイクで注入。"""
from __future__ import annotations

from hypothesis import given, strategies as st

import src.contact.service as service_module
from src.contact.models import Inquiry, InquiryCreate, InquiryStatus
from src.contact.repository import inquiry_to_item, item_to_inquiry
from src.contact.service import ContactService, compute_dedup_key


class _FakeRepo:
    def __init__(self, duplicate=False):
        self.saved = []
        self.notified_updates = []
        self._duplicate = duplicate

    def find_recent_duplicate(self, dedup_key, since_epoch):
        return self._duplicate

    def save(self, inquiry):
        self.saved.append(inquiry)

    def update_notified(self, inquiry_id, notified):
        self.notified_updates.append((inquiry_id, notified))


def _payload():
    return InquiryCreate(name="山田太郎", email="taro@example.com", message="体験申込したいです")


def test_submit_saves_and_notifies(monkeypatch):
    monkeypatch.setattr(service_module, "notify_new_inquiry", lambda *_: True)
    repo = _FakeRepo()
    svc = ContactService(repo)
    result = svc.submit(_payload(), created_at_epoch=1000, created_at_iso="2026-07-20T09:00:00+09:00")
    assert result["status"] == "accepted"
    assert result["duplicate"] is False
    assert len(repo.saved) == 1
    assert repo.saved[0].status == InquiryStatus.NEW
    assert repo.notified_updates == [(repo.saved[0].inquiry_id, True)]


def test_submit_duplicate_is_ignored(monkeypatch):
    monkeypatch.setattr(service_module, "notify_new_inquiry", lambda *_: True)
    repo = _FakeRepo(duplicate=True)
    svc = ContactService(repo)
    result = svc.submit(_payload(), created_at_epoch=1000, created_at_iso="2026-07-20T09:00:00+09:00")
    assert result["duplicate"] is True
    assert len(repo.saved) == 0  # 重複は保存しない


def test_submit_succeeds_even_if_notify_fails(monkeypatch):
    monkeypatch.setattr(service_module, "notify_new_inquiry", lambda *_: False)
    repo = _FakeRepo()
    svc = ContactService(repo)
    result = svc.submit(_payload(), created_at_epoch=1000, created_at_iso="2026-07-20T09:00:00+09:00")
    assert result["status"] == "accepted"       # 受付は成立（DB先行, Q-D1=A）
    assert repo.notified_updates == []           # notified 更新なし


def test_message_is_sanitized(monkeypatch):
    monkeypatch.setattr(service_module, "notify_new_inquiry", lambda *_: True)
    repo = _FakeRepo()
    svc = ContactService(repo)
    payload = InquiryCreate(name="太郎", email="t@example.com", message="<b>hi</b>")
    svc.submit(payload, created_at_epoch=1, created_at_iso="x")
    assert "<b>" not in repo.saved[0].message


# ---- PBT: dedup_key は空白・大文字小文字の正規化で安定 ----
@given(email=st.emails(), message=st.text(min_size=1, max_size=100))
def test_dedup_key_normalization(email, message):
    k1 = compute_dedup_key(email, message)
    k2 = compute_dedup_key(f"  {email.upper()}  ", f"{message}  ")
    assert k1 == k2


# ---- PBT: Inquiry の item 変換往復 ----
@given(name=st.text(min_size=1, max_size=30), msg=st.text(min_size=1, max_size=100))
def test_inquiry_item_roundtrip(name, msg):
    inquiry = Inquiry(
        inquiry_id="i1", name=name, email="a@example.com", message=msg,
        status=InquiryStatus.NEW, created_at="x", created_at_epoch=1, dedup_key="d",
    )
    restored = item_to_inquiry(inquiry_to_item(inquiry))
    assert restored.name == inquiry.name
    assert restored.message == inquiry.message
    assert restored.status == inquiry.status
