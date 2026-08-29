"""アプリ例外とグローバルエラーハンドリング（SECURITY-15 / SECURITY-09）。

- fail-closed: 例外時は拒否・汎用メッセージ。内部詳細を利用者に露出しない。
- グローバルハンドラで未捕捉例外を捕捉し、安全な HTTP 応答へ変換する。
"""
from __future__ import annotations

import json
from typing import Callable

from src.common.logging import get_logger, mask_pii

logger = get_logger("iyf.errors")


class AppError(Exception):
    """業務・入力エラーの基底。status_code と公開用メッセージを持つ。"""

    status_code = 400
    public_message = "リクエストを処理できませんでした。"

    def __init__(self, public_message: str | None = None):
        if public_message:
            self.public_message = public_message
        super().__init__(self.public_message)


class ValidationError(AppError):
    status_code = 400
    public_message = "入力内容に誤りがあります。"


class NotFoundError(AppError):
    status_code = 404
    public_message = "対象が見つかりません。"


class UnauthorizedError(AppError):
    status_code = 401
    public_message = "認証が必要です。"


class ForbiddenError(AppError):
    status_code = 403
    public_message = "アクセスが許可されていません。"


class ConflictError(AppError):
    """状態衝突（重複 email・プロフィール未完了・自己/最後の admin 無効化など）。"""

    status_code = 409
    public_message = "現在の状態では実行できません。"


class UnprocessableError(AppError):
    """入力は妥当だが業務ルール上処理できない（公開に必須項目が欠落 等）。"""

    status_code = 422
    public_message = "この内容では処理できません。"


class RateLimitedError(AppError):
    status_code = 429
    public_message = "リクエストが多すぎます。しばらくしてお試しください。"


def _cors_headers(origin: str | None) -> dict:
    """レスポンス共通ヘッダ。

    CORS（Access-Control-Allow-Origin 等）は **API Gateway(HTTP API) の
    CorsConfiguration に一本化**する（Lambda 側で付与すると二重ヘッダになり
    ブラウザが拒否するため）。ここではセキュリティ補助ヘッダのみ付与する。
    origin 引数は後方互換のため残すが未使用。
    """
    _ = origin
    return {
        "Content-Type": "application/json; charset=utf-8",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    }


def make_response(status_code: int, body: dict, origin: str | None = None) -> dict:
    """API Gateway(HTTP API) 互換のレスポンスを生成する。"""
    return {
        "statusCode": status_code,
        "headers": _cors_headers(origin),
        "body": json.dumps(body, ensure_ascii=False),
    }


def with_error_handling(handler: Callable) -> Callable:
    """ハンドラをラップするグローバルエラーハンドラ。

    - AppError は対応する status_code＋公開メッセージへ。
    - それ以外の例外は 500＋汎用メッセージ（内部詳細は露出しない, fail-closed）。
    """

    def wrapper(event: dict, context: object) -> dict:
        correlation_id = _extract_correlation_id(event, context)
        origin = _extract_origin(event)
        try:
            return handler(event, context)
        except AppError as exc:
            logger.warning(
                "handled app error",
                extra={"correlation_id": correlation_id, "status_code": exc.status_code},
            )
            return make_response(exc.status_code, {"error": exc.public_message}, origin)
        except Exception:  # noqa: BLE001 — 最終防衛線。詳細はログのみ。
            logger.error(
                "unhandled error",
                extra={"correlation_id": correlation_id, "status_code": 500},
                exc_info=True,
            )
            return make_response(
                500, {"error": "サーバー側で問題が発生しました。"}, origin
            )

    return wrapper


def _extract_correlation_id(event: dict, context: object) -> str:
    ctx = event.get("requestContext", {}) if isinstance(event, dict) else {}
    request_id = ctx.get("requestId")
    if request_id:
        return str(request_id)
    return str(getattr(context, "aws_request_id", "-"))


def _extract_origin(event: dict) -> str | None:
    if not isinstance(event, dict):
        return None
    headers = event.get("headers") or {}
    # HTTP API はヘッダ名を小文字化する。
    return headers.get("origin") or headers.get("Origin")


# 利用側の利便のため再エクスポート。
__all__ = [
    "AppError",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "UnprocessableError",
    "RateLimitedError",
    "make_response",
    "with_error_handling",
    "mask_pii",
]
