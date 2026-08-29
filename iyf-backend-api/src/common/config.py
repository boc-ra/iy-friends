"""設定読み込み。

非機密の設定は環境変数から、機密（SES 設定など）は SSM Parameter Store
（SecureString）から取得する（SECURITY-12: 平文/ハードコード禁止）。

- リージョンは JST 運用の東京固定（ap-northeast-1）。
- SSM 値は取得後プロセス内でキャッシュし、呼び出し回数を抑える（低コスト）。
"""
from __future__ import annotations

import os
from functools import lru_cache

import boto3

# ---- 非機密設定（環境変数） -------------------------------------------------

AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
STAGE = os.environ.get("STAGE", "prod")
TIMEZONE = "Asia/Tokyo"  # JST 固定（Q-F4=A）

# DynamoDB テーブル名（SAM から環境変数で注入）。デフォルトはローカル/テスト用。
TABLE_POSTS = os.environ.get("TABLE_POSTS", "Posts")
TABLE_NOTICES = os.environ.get("TABLE_NOTICES", "Notices")
TABLE_EVENTS = os.environ.get("TABLE_EVENTS", "Events")
TABLE_INQUIRIES = os.environ.get("TABLE_INQUIRIES", "Inquiries")
TABLE_USERS = os.environ.get("TABLE_USERS", "Users")

# 公開一覧のページサイズ（Q-F6=A）。
PAGE_SIZE = int(os.environ.get("PAGE_SIZE", "10"))

# 問い合わせの軽量冪等ウィンドウ（秒）。同一 email+message の短時間重複を無視。
CONTACT_DEDUP_WINDOW_SECONDS = int(os.environ.get("CONTACT_DEDUP_WINDOW_SECONDS", "300"))

# CORS 許可オリジン（カンマ区切り。SECURITY-08: ワイルドカード不可）。
_ALLOWED = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _ALLOWED.split(",") if o.strip()]

# SSM パラメータのパス接頭辞。
_SSM_PREFIX = os.environ.get("SSM_PREFIX", f"/iyf/{STAGE}")


@lru_cache(maxsize=32)
def get_secure_parameter(name: str) -> str:
    """SSM Parameter Store（SecureString）から機密設定を取得する。

    name は接頭辞なしの相対名（例: "ses/notify_to"）。復号して返す。
    """
    client = boto3.client("ssm", region_name=AWS_REGION)
    full_name = f"{_SSM_PREFIX}/{name}"
    resp = client.get_parameter(Name=full_name, WithDecryption=True)
    return resp["Parameter"]["Value"]


def get_ses_notify_recipient() -> str:
    """問い合わせ通知の送信先アドレス（機密扱いで SSM 管理）。"""
    return get_secure_parameter("ses/notify_to")


def get_ses_sender() -> str:
    """問い合わせ通知の送信元アドレス（SES 検証済み）。"""
    return get_secure_parameter("ses/sender")
