"""auth リポジトリ（Users テーブル）。

- PK=user_id（Cognito sub）。email 一意性は Cognito が担保するため email GSI は持たない。
- listUsers は Users が極小（≤10）につき Scan（限定用途, nfr-design-patterns-phase2 §2.2）。
"""
from __future__ import annotations

from src.auth.models import ProfileState, Role, UserProfile, UserStatus
from src.common.config import TABLE_USERS
from src.common.db import Repository


def profile_to_item(profile: UserProfile) -> dict:
    item = profile.model_dump()
    # enum は値（文字列）で保存。
    item["role"] = profile.role.value
    item["status"] = profile.status.value
    item["profile_state"] = profile.profile_state.value
    # None 属性は保存しない（DynamoDB の空値回避）。
    return {k: v for k, v in item.items() if v is not None}


def item_to_profile(item: dict) -> UserProfile:
    return UserProfile.model_validate(item)


class UserProfileRepository(Repository):
    def __init__(self):
        super().__init__(TABLE_USERS)

    def get(self, user_id: str) -> UserProfile | None:  # type: ignore[override]
        item = super().get({"user_id": user_id})
        return item_to_profile(item) if item else None

    def put_profile(self, profile: UserProfile) -> None:
        self.put(profile_to_item(profile))

    def update_profile_fields(self, user_id: str, updates: dict) -> None:
        self.update_item({"user_id": user_id}, updates)

    def list_all(self) -> list[UserProfile]:
        """管理ユーザー一覧（Scan≤10）。"""
        items = self.scan_all(limit=100)
        return [item_to_profile(i) for i in items]

    def count_active_admins(self) -> int:
        """有効な admin の数（最後の admin 保護に使用）。"""
        n = 0
        for p in self.list_all():
            if p.role == Role.ADMIN and p.status == UserStatus.ACTIVE:
                n += 1
        return n
