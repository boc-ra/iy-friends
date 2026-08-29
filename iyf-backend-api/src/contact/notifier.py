"""SES 通知（同期・ベストエフォート, Q-D1=A）。

送信失敗は例外を投げず False を返す（受付自体は DB 保存で成立）。
送信先/送信元は SSM から取得（機密, SECURITY-12）。
"""
from __future__ import annotations

from functools import lru_cache

import boto3
from botocore.config import Config

from src.common.config import (
    AWS_REGION,
    get_ses_notify_recipient,
    get_ses_sender,
)
from src.common.logging import get_logger

logger = get_logger("iyf.contact.notifier")

_BOTO_CONFIG = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 2, "mode": "standard"},
)


@lru_cache(maxsize=1)
def _ses_client():
    return boto3.client("ses", config=_BOTO_CONFIG)


def notify_new_inquiry(inquiry_id: str, name: str) -> bool:
    """新規問い合わせを管理者へ通知。成功=True / 失敗=False（例外送出しない）。

    本文に PII（email/message 全文）は含めない。詳細は管理画面で確認する方針。
    """
    try:
        sender = get_ses_sender()
        recipient = get_ses_notify_recipient()
        subject = "【IYフレンズ】新しいお問い合わせを受け付けました"
        body = (
            "新しいお問い合わせを受け付けました。\n"
            f"受付ID: {inquiry_id}\n"
            f"お名前: {name}\n\n"
            "内容は管理画面よりご確認ください。"
        )
        _ses_client().send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        return True
    except Exception:  # noqa: BLE001 — ベストエフォート。失敗はログのみ。
        logger.error("SES notify failed", extra={"event": {"inquiry_id": inquiry_id}}, exc_info=True)
        return False
