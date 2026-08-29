"""content サービス（公開読み取り＋管理系のビジネスロジック）。

公開系（Phase 1）:
- 一覧: published のみ・新しい順・10件/ページ（Q-F6=A）。
- 詳細: published のみ公開（draft は 404 扱いで存在を隠す, BR-STATE/BR-SEC）。

管理系（Phase 2, US-07/09）:
- 認可: ロール(handler の require_role) ＋ オーナー(require_owner, IDOR 防止)。
- 状態遷移: draft ⇄ published（BR-STATE）。公開時は必須項目検証・publishedAt 補完。
- 一覧: draft+published（BR-LIST）。Editor の draft は自分のみ可視。
"""
from __future__ import annotations

import uuid

from src.common.audit import record_change
from src.common.auth import Principal, require_owner
from src.common.config import PAGE_SIZE
from src.common.errors import NotFoundError, UnprocessableError
from src.common.validation import sanitize_richtext, sanitize_text
from src.content.models import (
    Notice,
    NoticeInput,
    Post,
    PostInput,
    PublishStatus,
    admin_summary,
)
from src.content.repository import NoticeRepository, PostRepository


class ContentService:
    def __init__(
        self,
        post_repo: PostRepository | None = None,
        notice_repo: NoticeRepository | None = None,
    ):
        self._posts = post_repo or PostRepository()
        self._notices = notice_repo or NoticeRepository()

    # ---- ブログ記事（US-01/04/05/06） ----

    def list_posts(self, *, start_key: dict | None = None) -> dict:
        posts, next_key = self._posts.list_published(limit=PAGE_SIZE, start_key=start_key)
        return {
            "items": [p.to_summary() for p in posts],
            "next_cursor": next_key,
        }

    def get_post(self, post_id: str) -> Post:
        post = self._posts.get_post(post_id)
        if post is None or not post.is_public():
            # draft/存在しないは同じ 404（存在秘匿, BR-SEC）。
            raise NotFoundError()
        return post

    # ---- お知らせ（US-08） ----

    def list_notices(self, *, start_key: dict | None = None) -> dict:
        notices, next_key = self._notices.list_published(limit=PAGE_SIZE, start_key=start_key)
        return {
            "items": [n.to_summary() for n in notices],
            "next_cursor": next_key,
        }

    def get_notice(self, notice_id: str) -> Notice:
        notice = self._notices.get_notice(notice_id)
        if notice is None or not notice.is_public():
            raise NotFoundError()
        return notice

    # ================= 管理系（Phase 2） =================

    # ---- ブログ記事 ----

    def create_post(
        self, *, author_id: str, author_display_name: str, data: PostInput,
        now_iso: str, now_epoch: int,
    ) -> dict:
        post = Post(
            post_id=str(uuid.uuid4()),
            title=sanitize_text(data.title),
            body=sanitize_richtext(data.body),
            author_display_name=author_display_name,
            author_id=author_id,
            category=data.category,
            status=data.status,
            created_at=now_iso,
            updated_at=now_iso,
            updated_at_epoch=now_epoch,
        )
        self._apply_publish_fields(post, data.status, now_iso, now_epoch, publishing=True)
        self._posts.save(post)
        record_change(
            entity="Post", entity_id=post.post_id, action="create",
            actor=author_id, before=None, after={"status": post.status.value},
        )
        return post.model_dump()

    def update_post(
        self, principal: Principal, post_id: str, data: PostInput,
        *, now_iso: str, now_epoch: int,
    ) -> dict:
        post = self._posts.get_post(post_id)
        if post is None:
            raise NotFoundError()
        require_owner(principal, post.author_id)
        before_status = post.status.value
        post.title = sanitize_text(data.title)
        post.body = sanitize_richtext(data.body)
        post.category = data.category
        post.updated_at = now_iso
        post.updated_at_epoch = now_epoch
        self._apply_publish_fields(post, data.status, now_iso, now_epoch, publishing=True)
        self._posts.save(post)
        record_change(
            entity="Post", entity_id=post_id, action="update",
            actor=principal.sub, before={"status": before_status}, after={"status": post.status.value},
        )
        return post.model_dump()

    def delete_post(self, principal: Principal, post_id: str) -> None:
        post = self._posts.get_post(post_id)
        if post is None:
            raise NotFoundError()
        require_owner(principal, post.author_id)   # Editor は自記事のみ（Q1=A）
        self._posts.delete_post(post_id)
        record_change(
            entity="Post", entity_id=post_id, action="delete",
            actor=principal.sub, before={"status": post.status.value}, after=None,
        )

    def set_post_status(
        self, principal: Principal, post_id: str, status: PublishStatus,
        *, now_iso: str, now_epoch: int,
    ) -> dict:
        post = self._posts.get_post(post_id)
        if post is None:
            raise NotFoundError()
        require_owner(principal, post.author_id)   # Editor は自記事のみ（Q2=A）
        before_status = post.status.value
        post.updated_at = now_iso
        post.updated_at_epoch = now_epoch
        self._apply_publish_fields(post, status, now_iso, now_epoch, publishing=True)
        self._posts.save(post)
        record_change(
            entity="Post", entity_id=post_id, action=f"set_status:{status.value}",
            actor=principal.sub, before={"status": before_status}, after={"status": status.value},
        )
        return post.model_dump()

    def get_post_admin(self, principal: Principal, post_id: str) -> dict:
        post = self._posts.get_post(post_id)
        if post is None:
            raise NotFoundError()
        # draft は作成者本人か admin のみ閲覧可（他人の未公開下書きは秘匿, BR-LIST-02）。
        if not post.is_public() and not principal.is_admin() and post.author_id != principal.sub:
            raise NotFoundError()
        return post.model_dump()

    def list_posts_admin(
        self, principal: Principal, *, status: str | None = None, start_key: dict | None = None
    ) -> dict:
        items, next_key = self._list_admin(
            self._posts, principal, status=status, start_key=start_key,
        )
        return {"items": [admin_summary(p) for p in items], "next_cursor": next_key}

    # ---- お知らせ ----

    def create_notice(
        self, *, author_id: str, author_display_name: str, data: NoticeInput,
        now_iso: str, now_epoch: int,
    ) -> dict:
        notice = Notice(
            notice_id=str(uuid.uuid4()),
            title=sanitize_text(data.title),
            body=sanitize_richtext(data.body),
            author_display_name=author_display_name,
            author_id=author_id,
            status=data.status,
            created_at=now_iso,
            updated_at=now_iso,
            updated_at_epoch=now_epoch,
        )
        self._apply_publish_fields(notice, data.status, now_iso, now_epoch, publishing=True)
        self._notices.save(notice)
        record_change(
            entity="Notice", entity_id=notice.notice_id, action="create",
            actor=author_id, before=None, after={"status": notice.status.value},
        )
        return notice.model_dump()

    def update_notice(
        self, principal: Principal, notice_id: str, data: NoticeInput,
        *, now_iso: str, now_epoch: int,
    ) -> dict:
        notice = self._notices.get_notice(notice_id)
        if notice is None:
            raise NotFoundError()
        require_owner(principal, notice.author_id)
        before_status = notice.status.value
        notice.title = sanitize_text(data.title)
        notice.body = sanitize_richtext(data.body)
        notice.updated_at = now_iso
        notice.updated_at_epoch = now_epoch
        self._apply_publish_fields(notice, data.status, now_iso, now_epoch, publishing=True)
        self._notices.save(notice)
        record_change(
            entity="Notice", entity_id=notice_id, action="update",
            actor=principal.sub, before={"status": before_status}, after={"status": notice.status.value},
        )
        return notice.model_dump()

    def delete_notice(self, principal: Principal, notice_id: str) -> None:
        notice = self._notices.get_notice(notice_id)
        if notice is None:
            raise NotFoundError()
        require_owner(principal, notice.author_id)
        self._notices.delete_notice(notice_id)
        record_change(
            entity="Notice", entity_id=notice_id, action="delete",
            actor=principal.sub, before={"status": notice.status.value}, after=None,
        )

    def set_notice_status(
        self, principal: Principal, notice_id: str, status: PublishStatus,
        *, now_iso: str, now_epoch: int,
    ) -> dict:
        notice = self._notices.get_notice(notice_id)
        if notice is None:
            raise NotFoundError()
        require_owner(principal, notice.author_id)
        before_status = notice.status.value
        notice.updated_at = now_iso
        notice.updated_at_epoch = now_epoch
        self._apply_publish_fields(notice, status, now_iso, now_epoch, publishing=True)
        self._notices.save(notice)
        record_change(
            entity="Notice", entity_id=notice_id, action=f"set_status:{status.value}",
            actor=principal.sub, before={"status": before_status}, after={"status": status.value},
        )
        return notice.model_dump()

    def get_notice_admin(self, principal: Principal, notice_id: str) -> dict:
        notice = self._notices.get_notice(notice_id)
        if notice is None:
            raise NotFoundError()
        if not notice.is_public() and not principal.is_admin() and notice.author_id != principal.sub:
            raise NotFoundError()
        return notice.model_dump()

    def list_notices_admin(
        self, principal: Principal, *, status: str | None = None, start_key: dict | None = None
    ) -> dict:
        items, next_key = self._list_admin(
            self._notices, principal, status=status, start_key=start_key,
        )
        return {"items": [admin_summary(n) for n in items], "next_cursor": next_key}

    # ---- 共通ヘルパ ----

    @staticmethod
    def _apply_publish_fields(entity, new_status: PublishStatus, now_iso, now_epoch, *, publishing):
        """状態遷移に伴う published_at 補完と必須項目検証（BR-STATE）。"""
        if new_status == PublishStatus.PUBLISHED:
            # 公開必須項目（サニタイズ後に本文が非空）。
            if not entity.title.strip() or not entity.body.strip():
                raise UnprocessableError("公開にはタイトルと本文が必要です。")
            if not entity.published_at:
                entity.published_at = now_iso
                entity.published_at_epoch = now_epoch
        entity.status = new_status

    def _list_admin(self, repo, principal: Principal, *, status: str | None, start_key: dict | None):
        """管理系一覧の可視範囲を適用（BR-LIST-02）。

        - status 指定あり: その状態のみ。
        - 指定なし: published + draft を結合（draft は Editor 時に自分のみ）。
        """
        limit = PAGE_SIZE
        if status is not None:
            items, next_key = repo.list_by_status(status, limit=limit, start_key=start_key)
            items = self._filter_visible_drafts(items, principal)
            return items, next_key
        # 指定なし: published を主に、draft を補完（簡易・小規模前提）。
        pub, next_key = repo.list_by_status(PublishStatus.PUBLISHED.value, limit=limit, start_key=start_key)
        drafts, _ = repo.list_by_status(PublishStatus.DRAFT.value, limit=limit, start_key=None)
        drafts = self._filter_visible_drafts(drafts, principal)
        combined = (drafts + pub)[:limit]
        return combined, next_key

    @staticmethod
    def _filter_visible_drafts(items, principal: Principal):
        """Editor は他人の draft を見られない（自分の draft と published は可）。"""
        if principal.is_admin():
            return items
        visible = []
        for it in items:
            if it.is_public() or it.author_id == principal.sub:
                visible.append(it)
        return visible
