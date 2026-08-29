"""auth ドメインモデル（UserProfile ほか）。

- 認証情報は Cognito が保持。U3 は role/displayName/status/profileState を扱う。
- displayName は招待直後 null(pending)、初回ログインで本人が設定（Q5=B, BR-USER-02）。
- role は Cognito グループを正とし、ここはミラー（BR-AUTH-03）。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ProfileState(str, Enum):
    PENDING = "pending"      # 招待済・displayName 未設定（投稿不可）
    COMPLETE = "complete"    # 初回ログインで displayName 設定済（投稿可）


class UserProfile(BaseModel):
    """管理ユーザーのプロファイル（DynamoDB Users テーブル）。"""

    user_id: str                                  # Cognito sub（PK）
    email: str
    display_name: str | None = None               # pending 中は None
    role: Role = Role.EDITOR
    status: UserStatus = UserStatus.ACTIVE
    profile_state: ProfileState = ProfileState.PENDING
    invited_by: str | None = None
    created_at: str | None = None                 # ISO8601(JST)
    updated_at: str | None = None

    def is_postable(self) -> bool:
        """投稿・公開が可能な状態か（active かつ profile 完了）。"""
        return self.status == UserStatus.ACTIVE and self.profile_state == ProfileState.COMPLETE

    def to_summary(self) -> dict:
        """管理一覧用の DTO（PII 最小: email は管理目的で表示）。"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role.value,
            "status": self.status.value,
            "profile_state": self.profile_state.value,
            "created_at": self.created_at,
        }


# ---- 入力 DTO（SECURITY-05） ----

class InviteRequest(BaseModel):
    """編集者招待リクエスト（Admin）。"""

    email: EmailStr


class CompleteProfileRequest(BaseModel):
    """初回ログイン時の自己プロファイル設定。"""

    display_name: str = Field(min_length=1, max_length=40)


class SetUserStatusRequest(BaseModel):
    """ユーザー有効/無効の切替（Admin）。"""

    status: UserStatus
