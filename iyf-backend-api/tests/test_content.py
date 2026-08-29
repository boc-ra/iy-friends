"""content モデル・サービス・シリアライズ往復（PBT）テスト。"""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.common.errors import NotFoundError
from src.content.models import Notice, Post, PublishStatus
from src.content.repository import item_to_post, post_to_item
from src.content.service import ContentService


class _FakePostRepo:
    def __init__(self, posts):
        self._by_id = {p.post_id: p for p in posts}
        self._published = [p for p in posts if p.is_public()]

    def get_post(self, post_id):
        return self._by_id.get(post_id)

    def list_published(self, *, limit, start_key=None):
        return self._published[:limit], None


class _FakeNoticeRepo:
    def __init__(self, notices):
        self._by_id = {n.notice_id: n for n in notices}
        self._published = [n for n in notices if n.is_public()]

    def get_notice(self, nid):
        return self._by_id.get(nid)

    def list_published(self, *, limit, start_key=None):
        return self._published[:limit], None


def _post(pid, status):
    return Post(
        post_id=pid, title="t", body="b", author_display_name="コーチ",
        status=status, published_at="2026-07-20T09:00:00+09:00", published_at_epoch=1,
    )


def test_get_post_hides_draft_as_404():
    svc = ContentService(_FakePostRepo([_post("p1", PublishStatus.DRAFT)]), _FakeNoticeRepo([]))
    with pytest.raises(NotFoundError):
        svc.get_post("p1")


def test_get_post_returns_published():
    svc = ContentService(_FakePostRepo([_post("p1", PublishStatus.PUBLISHED)]), _FakeNoticeRepo([]))
    assert svc.get_post("p1").post_id == "p1"


def test_list_posts_only_published_summaries():
    posts = [_post("p1", PublishStatus.PUBLISHED), _post("p2", PublishStatus.DRAFT)]
    svc = ContentService(_FakePostRepo(posts), _FakeNoticeRepo([]))
    result = svc.list_posts()
    ids = [i["post_id"] for i in result["items"]]
    assert ids == ["p1"]
    assert "body" not in result["items"][0]  # 一覧に本文を含めない


# ---- PBT: Post の item 変換往復で本質フィールドが保存される ----
@given(
    title=st.text(min_size=1, max_size=50),
    author=st.text(min_size=1, max_size=30),
    published=st.booleans(),
)
def test_post_item_roundtrip(title, author, published):
    status = PublishStatus.PUBLISHED if published else PublishStatus.DRAFT
    post = Post(
        post_id="p", title=title, body="body", author_display_name=author,
        status=status, published_at_epoch=10,
    )
    restored = item_to_post(post_to_item(post))
    assert restored.title == post.title
    assert restored.author_display_name == post.author_display_name
    assert restored.status == post.status
