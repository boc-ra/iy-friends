"""Cognito 連携（cognito-idp）。副作用を隔離し、テストでスタブ注入可能にする。

- boto3 の限定リトライを設定（無限リトライ禁止, NFR-U3-REL）。
- 例外は業務エラーへマッピング（重複 email → ConflictError）。
- 招待は AdminCreateUser（招待メール＋仮パスワード, Q4=A）。role は editor グループ。
"""
from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.common.config import AWS_REGION
from src.common.errors import AppError, ConflictError

_BOTO_CONFIG = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
)


@lru_cache(maxsize=1)
def _default_client():
    return boto3.client("cognito-idp", config=_BOTO_CONFIG)


class CognitoError(AppError):
    """Cognito 操作の失敗（fail-closed で 500 相当）。"""

    status_code = 502
    public_message = "認証基盤との連携に失敗しました。"


class CognitoClient:
    """cognito-idp の薄いラッパ。user_pool_id を束ねる。"""

    def __init__(self, user_pool_id: str, client=None):
        self._pool = user_pool_id
        self._client = client or _default_client()

    def admin_create_user(self, email: str) -> str:
        """招待（AdminCreateUser）。招待メール＋仮パスワードを送付し、sub を返す。"""
        try:
            resp = self._client.admin_create_user(
                UserPoolId=self._pool,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                ],
                DesiredDeliveryMediums=["EMAIL"],
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in ("UsernameExistsException", "AliasExistsException"):
                raise ConflictError("このメールアドレスは既に登録されています。")
            raise CognitoError()
        return _extract_sub(resp.get("User", {}))

    def add_to_group(self, sub_or_username: str, group: str) -> None:
        try:
            self._client.admin_add_user_to_group(
                UserPoolId=self._pool, Username=sub_or_username, GroupName=group,
            )
        except ClientError:
            raise CognitoError()

    def disable_user(self, username: str) -> None:
        try:
            self._client.admin_disable_user(UserPoolId=self._pool, Username=username)
        except ClientError:
            raise CognitoError()

    def enable_user(self, username: str) -> None:
        try:
            self._client.admin_enable_user(UserPoolId=self._pool, Username=username)
        except ClientError:
            raise CognitoError()


def _extract_sub(user: dict) -> str:
    """AdminCreateUser 応答から sub 属性を取り出す。無ければ Username を用いる。"""
    for attr in user.get("Attributes", []):
        if attr.get("Name") == "sub":
            return str(attr.get("Value"))
    return str(user.get("Username", ""))
