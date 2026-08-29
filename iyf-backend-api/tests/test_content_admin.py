"""content 管理系: オーナー認可(IDOR)・状態遷移・draft 可視範囲。"""
from __future__ import annotations

import pytest

from src.common.auth import ROLE_ADMIN, ROLE_EDITOR, Principal
from src.common.errors import ForbiddenError, NotFoundError, UnprocessableError
from src.content.models import Post, PostInput, PublishStatus
from src.content.service import ContentService


class _FakePostRepo:
    def __init__(self, posts=None):
        self._by_id = {p.post_id: p for p in (posts or [])}
        self.saved = []
        self.deleted = []

    def get_post(self, post_id):
        return self._by_id.get(post_id)

    def save(self, post):
        self._by_id[post.post_id] = post
        self.saved.append(post)

    def delete_post(self, post_id):
        self._by_id.pop(post_id, None)
        self.deleted.append(post_id)

    def list_by_status(self, status_value, *, limit, start_key=None):
        items = [p for p in self._by_id.values() if p.status.value == status_value]
        return items[:limit], None


class _NoNoticeRepo:
    def list_by_status(self, *a, **k):
        return [], None


def _editor(sub="ed1"):
    return Principal(sub=sub, role=ROLE_EDITOR, groups=("editor",))


def _admin(sub="ad1"):
    return Principal(sub=sub, role=ROLE_ADMIN, groups=("admin",))


def _post(pid, author_id, status=PublishStatus.DRAFT):
    return Post(post_id=pid, title="t", body="b", author_display_name="コーチ",
                author_id=author_id, status=status)


def _svc(posts):
    return ContentService(_FakePostRepo(posts), _NoNoticeRepo())


# ---- 作成 ----

def test_create_post_draft():
    repo = _FakePostRepo()
    svc = ContentService(repo, _NoNoticeRepo())
    out = svc.create_post(
        author_id="ed1", author_display_name="コーチ",
        data=PostInput(title="やあ", body="本文", status=PublishStatus.DRAFT),
        now_iso="2026-07-20T09:00:00+09:00", now_epoch=100,
    )
    assert out["status"] == "draft"
    assert out["author_id"] == "ed1"
    assert repo.saved[0].updated_at_epoch == 100


def test_create_post_published_requires_body():
    svc = ContentService(_FakePostRepo(), _NoNoticeRepo())
    with pytest.raises(UnprocessableError):
        svc.create_post(
            author_id="ed1", author_display_name="コーチ",
            data=PostInput(title="題", body="   ", status=PublishStatus.PUBLISHED),
            now_iso="t", now_epoch=1,
        )


def test_create_post_published_sets_published_at():
    repo = _FakePostRepo()
    svc = ContentService(repo, _NoNoticeRepo())
    svc.create_post(
        author_id="ed1", author_display_name="コーチ",
        data=PostInput(title="題", body="内容", status=PublishStatus.PUBLISHED),
        now_iso="2026-07-20T09:00:00+09:00", now_epoch=555,
    )
    saved = repo.saved[0]
    assert saved.published_at == "2026-07-20T09:00:00+09:00"
    assert saved.published_at_epoch == 555


# ---- オーナー認可（IDOR, SECURITY-08） ----

def test_editor_cannot_update_others_post():
    svc = _svc([_post("p1", author_id="other")])
    with pytest.raises(ForbiddenError):
        svc.update_post(_editor("ed1"), "p1", PostInput(title="x", body="y"), now_iso="t", now_epoch=1)


def test_editor_can_update_own_post():
    svc = _svc([_post("p1", author_id="ed1")])
    out = svc.update_post(_editor("ed1"), "p1", PostInput(title="new", body="y"), now_iso="t", now_epoch=2)
    assert out["title"] == "new"


def test_editor_cannot_delete_others_post():
    svc = _svc([_post("p1", author_id="other")])
    with pytest.raises(ForbiddenError):
        svc.delete_post(_editor("ed1"), "p1")


def test_editor_can_delete_own_post():
    repo = _FakePostRepo([_post("p1", author_id="ed1")])
    svc = ContentService(repo, _NoNoticeRepo())
    svc.delete_post(_editor("ed1"), "p1")
    assert repo.deleted == ["p1"]


def test_admin_can_update_any_post():
    svc = _svc([_post("p1", author_id="someone")])
    out = svc.update_post(_admin(), "p1", PostInput(title="z", body="y"), now_iso="t", now_epoch=3)
    assert out["title"] == "z"


def test_update_missing_post_404():
    svc = _svc([])
    with pytest.raises(NotFoundError):
        svc.update_post(_admin(), "nope", PostInput(title="z", body="y"), now_iso="t", now_epoch=1)


# ---- 状態遷移 ----

def test_set_status_publish_and_unpublish():
    repo = _FakePostRepo([_post("p1", author_id="ed1", status=PublishStatus.DRAFT)])
    svc = ContentService(repo, _NoNoticeRepo())
    out = svc.set_post_status(_editor("ed1"), "p1", PublishStatus.PUBLISHED, now_iso="t", now_epoch=9)
    assert out["status"] == "published"
    out2 = svc.set_post_status(_editor("ed1"), "p1", PublishStatus.DRAFT, now_iso="t", now_epoch=10)
    assert out2["status"] == "draft"


# ---- 一覧の draft 可視範囲（BR-LIST-02） ----

def test_editor_sees_only_own_draft_plus_published():
    posts = [
        _post("mine", author_id="ed1", status=PublishStatus.DRAFT),
        _post("theirs", author_id="ed2", status=PublishStatus.DRAFT),
        _post("pub", author_id="ed2", status=PublishStatus.PUBLISHED),
    ]
    svc = _svc(posts)
    result = svc.list_posts_admin(_editor("ed1"))
    ids = {i["post_id"] for i in result["items"]}
    assert "mine" in ids and "pub" in ids
    assert "theirs" not in ids


def test_admin_sees_all_drafts():
    posts = [
        _post("d1", author_id="ed1", status=PublishStatus.DRAFT),
        _post("d2", author_id="ed2", status=PublishStatus.DRAFT),
    ]
    svc = _svc(posts)
    result = svc.list_posts_admin(_admin(), status="draft")
    ids = {i["post_id"] for i in result["items"]}
    assert ids == {"d1", "d2"}


def test_get_post_admin_hides_others_draft():
    svc = _svc([_post("p1", author_id="ed2", status=PublishStatus.DRAFT)])
    with pytest.raises(NotFoundError):
        svc.get_post_admin(_editor("ed1"), "p1")
