"""入力検証ユーティリティ（SECURITY-05）。

- Pydantic モデルによるスキーマ検証を薄くラップし、失敗を ValidationError へ変換。
- 文字列の長さ上限・HTML エスケープ等の純粋関数を提供（PBT 対象）。
"""
from __future__ import annotations

import html
import json
from typing import Type, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from src.common.errors import ValidationError

TModel = TypeVar("TModel", bound=BaseModel)

# ペイロードサイズ上限（バイト）。ゲートウェイ側とは別のアプリ層防御。
MAX_BODY_BYTES = 64 * 1024


def parse_body(raw_body: str | None) -> dict:
    """リクエストボディ(JSON文字列)を辞書へ。サイズ上限・型を検証。"""
    if not raw_body:
        raise ValidationError("リクエスト本文が空です。")
    if len(raw_body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValidationError("リクエスト本文が大きすぎます。")
    try:
        data = json.loads(raw_body)
    except (ValueError, TypeError):
        raise ValidationError("リクエスト本文の形式が不正です。")
    if not isinstance(data, dict):
        raise ValidationError("リクエスト本文はオブジェクトである必要があります。")
    return data


def validate(model: Type[TModel], data: dict) -> TModel:
    """辞書を Pydantic モデルへ検証変換。失敗は ValidationError に統一。"""
    try:
        return model.model_validate(data)
    except PydanticValidationError:
        # 詳細（フィールド名等）は利用者へ露出しない（fail-closed）。
        raise ValidationError("入力内容に誤りがあります。")


def sanitize_text(value: str) -> str:
    """ユーザー入力テキストの HTML を無害化（XSS 対策, SECURITY-05）。

    純粋関数（PBT 対象）: 前後空白を除去し、HTML 特殊文字をエスケープする。
    """
    return html.escape(value.strip(), quote=True)


# リッチテキスト（WYSIWYG 由来）で許可するタグ/属性（allowlist, SECURITY-05）。
_ALLOWED_TAGS = [
    "p", "br", "strong", "b", "em", "i", "u", "s", "ul", "ol", "li",
    "a", "h2", "h3", "h4", "blockquote", "pre", "code", "hr", "span",
]
_ALLOWED_ATTRS = {"a": ["href", "title", "target", "rel"]}


def sanitize_richtext(value: str) -> str:
    """WYSIWYG 由来の本文を allowlist サニタイズ（XSS 対策, SECURITY-05）。

    bleach が利用可能なら allowlist で無害化。無い環境（テスト等）では
    保守的フォールバックとして `<script>`/`<style>` を除去しつつ HTML を
    エスケープする（安全側 = fail-closed）。
    """
    text = value.strip()
    try:
        import bleach  # 遅延 import（未導入環境でも import エラーにしない）

        return bleach.clean(
            text, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True
        )
    except ImportError:
        # フォールバック: タグをエスケープして無害化（表示は生テキスト寄りだが安全）。
        return html.escape(text, quote=True)


def clamp_limit(requested: int | None, default: int, maximum: int) -> int:
    """ページサイズを [1, maximum] に収める純粋関数（PBT 対象）。

    requested が None のときは default を用いるが、その場合も上限 maximum を超えない。
    """
    value = default if requested is None else requested
    if value < 1:
        return 1
    if value > maximum:
        return maximum
    return value
