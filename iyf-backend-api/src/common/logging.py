"""構造化ロギング（SECURITY-03）。

- JSON 形式・相関ID付きで CloudWatch Logs に出力。
- PII（email / message / name など）はログに出さない。マスク関数を提供。
"""
from __future__ import annotations

import json
import logging
import os
import sys

# PII とみなすキー（値をマスクする）。
_PII_KEYS = {"email", "message", "name", "password", "token", "authorization"}
_MASK = "***"


def _mask_value(key: str, value: object) -> object:
    if key.lower() in _PII_KEYS and value is not None:
        return _MASK
    return value


def mask_pii(data: dict) -> dict:
    """辞書内の PII 値をマスクした新しい辞書を返す（浅い階層＋1段ネスト対応）。"""
    masked: dict = {}
    for key, value in data.items():
        if isinstance(value, dict):
            masked[key] = mask_pii(value)
        else:
            masked[key] = _mask_value(key, value)
    return masked


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # 相関ID・追加フィールド（extra={"correlation_id": ...} 等）を取り込む。
        for field in ("correlation_id", "route", "status_code", "event"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "iyf") -> logging.Logger:
    """構造化 JSON ロガーを取得する。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
        logger.propagate = False
    return logger
