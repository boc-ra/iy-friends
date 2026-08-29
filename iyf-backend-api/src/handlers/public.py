"""公開エンドポイント（API Gateway HTTP API / Lambda proxy 統合）。

ルート（Phase 1）:
  GET  /posts                 記事一覧（published, 10件, カーソル）
  GET  /posts/{id}            記事詳細（published のみ）
  GET  /notices               お知らせ一覧
  GET  /notices/{id}          お知らせ詳細
  GET  /events                イベント一覧（日付昇順）
  GET  /events/{id}           イベント詳細
  POST /contact               問い合わせ送信

各ハンドラは:
  入力検証(SECURITY-05) → 公開/認可判定(SECURITY-08) → サービス → 汎用エラー整形(SECURITY-15)。
時刻は JST でここで確定し、サービスへ注入する（決定性）。
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone, timedelta

from src.calendar.service import CalendarService
from src.common import auth
from src.common.errors import (
    NotFoundError,
    ValidationError,
    make_response,
    with_error_handling,
)
from src.common.logging import get_logger
from src.common.validation import parse_body, validate
from src.contact.models import InquiryCreate
from src.contact.service import ContactService
from src.content.service import ContentService

logger = get_logger("iyf.handlers.public")

JST = timezone(timedelta(hours=9))

# サービスはコールドスタート時に一度だけ生成（再利用）。
_content = ContentService()
_calendar = CalendarService()
_contact = ContactService()


# ---- カーソル(pagination)エンコード ----------------------------------------

def _encode_cursor(key: dict | None) -> str | None:
    if not key:
        return None
    return base64.urlsafe_b64encode(json.dumps(key).encode("utf-8")).decode("ascii")


def _decode_cursor(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
    except (ValueError, TypeError):
        raise ValidationError("カーソルが不正です。")


def _query_param(event: dict, name: str) -> str | None:
    params = event.get("queryStringParameters") or {}
    return params.get(name)


def _path_param(event: dict, name: str) -> str:
    params = event.get("pathParameters") or {}
    value = params.get(name)
    if not value:
        raise ValidationError("パスパラメータが不足しています。")
    return value


def _route_key(event: dict) -> str:
    """HTTP API の routeKey（例 'GET /posts'）。無い場合は method+path から組み立て。"""
    rk = event.get("routeKey")
    if rk and rk != "$default":
        return rk
    ctx = event.get("requestContext", {}).get("http", {})
    return f"{ctx.get('method', 'GET')} {ctx.get('path', '/')}"


def _origin(event: dict) -> str | None:
    headers = event.get("headers") or {}
    return headers.get("origin") or headers.get("Origin")


# ---- 個別ルートロジック -----------------------------------------------------

def _list_posts(event):
    auth.require_public()
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _content.list_posts(start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_post(event):
    auth.require_public()
    post = _content.get_post(_path_param(event, "id"))
    return post.model_dump()


def _list_notices(event):
    auth.require_public()
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _content.list_notices(start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_notice(event):
    auth.require_public()
    notice = _content.get_notice(_path_param(event, "id"))
    return notice.model_dump()


def _list_events(event):
    auth.require_public()
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _calendar.list_events(start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_event(event):
    auth.require_public()
    ev = _calendar.get_event(_path_param(event, "id"))
    return ev.model_dump()


def _submit_contact(event):
    auth.require_public()
    data = parse_body(event.get("body"))
    payload = validate(InquiryCreate, data)
    now = datetime.now(JST)
    return _contact.submit(
        payload,
        created_at_epoch=int(now.timestamp()),
        created_at_iso=now.isoformat(),
    )


_ROUTES = {
    "GET /posts": (_list_posts, 200),
    "GET /posts/{id}": (_get_post, 200),
    "GET /notices": (_list_notices, 200),
    "GET /notices/{id}": (_get_notice, 200),
    "GET /events": (_list_events, 200),
    "GET /events/{id}": (_get_event, 200),
    "POST /contact": (_submit_contact, 201),
}


@with_error_handling
def handler(event: dict, context: object) -> dict:
    """Lambda エントリポイント。routeKey でディスパッチする。"""
    route = _route_key(event)
    origin = _origin(event)
    entry = _ROUTES.get(route)
    if entry is None:
        raise NotFoundError("ルートが見つかりません。")
    func, success_status = entry
    body = func(event)
    logger.info("request handled", extra={"route": route, "status_code": success_status})
    return make_response(success_status, body, origin)
