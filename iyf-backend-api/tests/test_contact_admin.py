"""contact 管理系: 一覧（status 絞り込み/全件）・状態更新（Admin）。"""
from __future__ import annotations

import pytest

from src.common.auth import ROLE_ADMIN, Principal
from src.common.errors import NotFoundError
from src.contact.models import Inquiry, InquiryStatus
from src.contact.service import ContactService


class _FakeInquiryRepo:
    def __init__(self, inquiries=None):
        self._by_id = {i.inquiry_id: i for i in (inquiries or [])}
        self.updated = []

    def get_inquiry(self, inquiry_id):
        return self._by_id.get(inquiry_id)

    def list_by_status(self, status_value, *, limit, start_key=None):
        items = [i for i in self._by_id.values() if i.status.value == status_value]
        return items[:limit], None

    def update_status(self, inquiry_id, status_value, updated_by, updated_at):
        inq = self._by_id[inquiry_id]
        data = inq.model_dump()
        data.update({"status": status_value, "updated_by": updated_by, "updated_at": updated_at})
        self._by_id[inquiry_id] = Inquiry.model_validate(data)
        self.updated.append((inquiry_id, status_value))


def _admin():
    return Principal(sub="ad1", role=ROLE_ADMIN, groups=("admin",))


def _inq(iid, status, epoch):
    return Inquiry(inquiry_id=iid, name="親", email="p@x.com", message="こんにちは",
                   status=status, created_at="2026-07-20T09:00:00+09:00",
                   created_at_epoch=epoch, dedup_key="k" + iid)


def test_list_inquiries_all_sorted_desc():
    repo = _FakeInquiryRepo([
        _inq("a", InquiryStatus.NEW, 100),
        _inq("b", InquiryStatus.DONE, 300),
        _inq("c", InquiryStatus.IN_PROGRESS, 200),
    ])
    svc = ContactService(repo)
    result = svc.list_inquiries()
    ids = [i["inquiry_id"] for i in result["items"]]
    assert ids == ["b", "c", "a"]   # created_at_epoch 降順


def test_list_inquiries_filter_by_status():
    repo = _FakeInquiryRepo([
        _inq("a", InquiryStatus.NEW, 100),
        _inq("b", InquiryStatus.DONE, 300),
    ])
    svc = ContactService(repo)
    result = svc.list_inquiries(status=InquiryStatus.NEW.value)
    assert [i["inquiry_id"] for i in result["items"]] == ["a"]


def test_get_inquiry_not_found():
    svc = ContactService(_FakeInquiryRepo())
    with pytest.raises(NotFoundError):
        svc.get_inquiry("missing")


def test_update_inquiry_status():
    repo = _FakeInquiryRepo([_inq("a", InquiryStatus.NEW, 100)])
    svc = ContactService(repo)
    out = svc.update_inquiry_status(_admin(), "a", InquiryStatus.DONE, now_iso="2026-07-20T10:00:00+09:00")
    assert out["status"] == "対応済"
    assert out["updated_by"] == "ad1"
    assert repo.updated == [("a", "対応済")]
