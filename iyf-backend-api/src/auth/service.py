"""auth サービス（招待・プロファイル完了・ユーザー管理）。

認可（ロール）は handler 層の require_role で担保する前提。本サービスは
業務ルール（自己/最後の admin 保護・プロファイル未完了の投稿不可）を担う。
Cognito と Repository は注入可能（テストでスタブ化）。
"""
from __future__ import annotations

from src.auth.cognito import CognitoClient
from src.auth.models import (
    ProfileState,
    Role,
    UserProfile,
    UserStatus,
)
from src.auth.repository import UserProfileRepository
from src.common.audit import record_change
from src.common.auth import Principal
from src.common.errors import ConflictError, NotFoundError
from src.common.validation import sanitize_text

_EDITOR_GROUP = "editor"


class AuthService:
    def __init__(
        self,
        repo: UserProfileRepository | None = None,
        cognito: CognitoClient | None = None,
    ):
        self._repo = repo or UserProfileRepository()
        self._cognito = cognito  # None の場合は招待/無効化を呼ぶ前に設定が必要。

    # ---- 招待（Admin） ----

    def invite_editor(self, actor: Principal, email: str, *, now_iso: str) -> dict:
        """編集者を招待。Cognito 作成→editor グループ→プロファイル stub 作成。"""
        assert self._cognito is not None, "CognitoClient not configured"
        normalized = email.strip().lower()
        sub = self._cognito.admin_create_user(normalized)   # 重複は ConflictError
        self._cognito.add_to_group(normalized, _EDITOR_GROUP)
        profile = UserProfile(
            user_id=sub,
            email=normalized,
            display_name=None,
            role=Role.EDITOR,
            status=UserStatus.ACTIVE,
            profile_state=ProfileState.PENDING,
            invited_by=actor.sub,
            created_at=now_iso,
            updated_at=now_iso,
        )
        self._repo.put_profile(profile)
        record_change(
            entity="User", entity_id=sub, action="invite",
            actor=actor.sub, before=None, after={"role": "editor", "state": "pending"},
        )
        return profile.to_summary()

    # ---- プロファイル完了（本人・初回ログイン） ----

    def complete_profile(self, principal: Principal, display_name: str, *, now_iso: str) -> dict:
        """初回ログイン後、本人が displayName を設定して pending を解除。"""
        profile = self._ensure_profile(principal, now_iso=now_iso)
        clean = sanitize_text(display_name)
        self._repo.update_profile_fields(
            principal.sub,
            {
                "display_name": clean,
                "profile_state": ProfileState.COMPLETE.value,
                "updated_at": now_iso,
            },
        )
        record_change(
            entity="User", entity_id=principal.sub, action="complete_profile",
            actor=principal.sub, before={"state": "pending"}, after={"state": "complete"},
        )
        updated = self._repo.get(principal.sub)
        return updated.to_summary() if updated else profile.to_summary()

    # ---- 一覧（Admin） ----

    def list_users(self) -> dict:
        return {"items": [p.to_summary() for p in self._repo.list_all()]}

    # ---- 有効/無効（Admin） ----

    def set_user_status(
        self, actor: Principal, user_id: str, status: UserStatus, *, now_iso: str
    ) -> dict:
        assert self._cognito is not None, "CognitoClient not configured"
        target = self._repo.get(user_id)
        if target is None:
            raise NotFoundError()

        if status == UserStatus.DISABLED:
            # 自己無効化の禁止（ロックアウト防止, BR-USER-04）。
            if user_id == actor.sub:
                raise ConflictError("自分自身は無効化できません。")
            # 最後の有効 admin の無効化を禁止。
            if target.role == Role.ADMIN and target.status == UserStatus.ACTIVE:
                if self._repo.count_active_admins() <= 1:
                    raise ConflictError("最後の管理者は無効化できません。")
            self._cognito.disable_user(target.email)
        else:
            self._cognito.enable_user(target.email)

        self._repo.update_profile_fields(
            user_id, {"status": status.value, "updated_at": now_iso}
        )
        record_change(
            entity="User", entity_id=user_id, action=f"set_status:{status.value}",
            actor=actor.sub, before={"status": target.status.value}, after={"status": status.value},
        )
        updated = self._repo.get(user_id)
        return updated.to_summary() if updated else {}

    # ---- 投稿可否ヘルパ（content/calendar から利用） ----

    def get_postable_profile(self, principal: Principal, *, now_iso: str) -> UserProfile:
        """投稿可能なプロファイルを返す。未完了/無効なら ConflictError。"""
        profile = self._ensure_profile(principal, now_iso=now_iso)
        if not profile.is_postable():
            raise ConflictError("プロフィール設定が完了していません。")
        return profile

    # ---- 内部 ----

    def _ensure_profile(self, principal: Principal, *, now_iso: str) -> UserProfile:
        """プロファイルを取得。存在しなければ stub を補完（Cognito 直作成 admin 対策）。"""
        profile = self._repo.get(principal.sub)
        if profile is not None:
            return profile
        role = Role.ADMIN if principal.is_admin() else Role.EDITOR
        stub = UserProfile(
            user_id=principal.sub,
            email=principal.sub,   # email 不明時は sub を暫定。complete 時に上書きされ得る。
            display_name=None,
            role=role,
            status=UserStatus.ACTIVE,
            profile_state=ProfileState.PENDING,
            created_at=now_iso,
            updated_at=now_iso,
        )
        self._repo.put_profile(stub)
        return stub
