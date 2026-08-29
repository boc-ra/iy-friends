"""管理エンドポイント（認証必須, API Gateway HTTP API / Lambda proxy 統合）。

認可（二層, nfr-design-patterns-phase2 §1.1）:
- 層1: API Gateway の Cognito JWT オーソライザ（署名/失効/aud/iss/exp 検証）。
- 層2（本ハンドラ）: require_authenticated → ルート別 require_role
         → サービス内 require_owner（IDOR 防止）。

時刻(JST)はここで確定し、サービスへ注入する（決定性）。
ロール: admin=全操作 / editor=ブログ・お知らせ・カレンダー（自リソースのみ編集）。
問い合わせ管理・ユーザー招待/管理は admin 専用。
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone

from src.auth.cognito import CognitoClient
from src.auth.models import (
    CompleteProfileRequest,
    InviteRequest,
    SetUserStatusRequest,
)
from src.auth.service import AuthService
from src.calendar.models import EventInput
from src.calendar.service import CalendarService
from src.common import auth
from src.common.auth import ROLE_ADMIN, ROLE_EDITOR
from src.common.config import STAGE
from src.common.errors import NotFoundError, ValidationError, make_response, with_error_handling
from src.common.logging import get_logger
from src.common.validation import parse_body, validate
from src.contact.models import InquiryStatusUpdate
from src.contact.service import ContactService
from src.content.models import NoticeInput, PostInput, StatusUpdate
from src.content.service import ContentService

logger = get_logger("iyf.handlers.admin")

JST = timezone(timedelta(hours=9))

# サービスはコールドスタート時に一度だけ生成（再利用）。
_content = ContentService()
_calendar = CalendarService()
_contact = ContactService()


def _auth_service() -> AuthService:
    """AuthService を遅延生成（USER_POOL_ID 環境変数から Cognito クライアント構成）。"""
    import os

    user_pool_id = os.environ.get("USER_POOL_ID", "")
    cognito = CognitoClient(user_pool_id) if user_pool_id else None
    return AuthService(cognito=cognito)


# ---- 補助 -------------------------------------------------------------------

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
    rk = event.get("routeKey")
    if rk and rk != "$default":
        return rk
    ctx = event.get("requestContext", {}).get("http", {})
    return f"{ctx.get('method', 'GET')} {ctx.get('path', '/')}"


def _origin(event: dict) -> str | None:
    headers = event.get("headers") or {}
    return headers.get("origin") or headers.get("Origin")


def _now():
    now = datetime.now(JST)
    return now.isoformat(), int(now.timestamp())


def _event_date_epoch(iso: str) -> int:
    """イベント日付(ISO8601)を epoch 秒へ。不正な形式は 400。"""
    try:
        return int(datetime.fromisoformat(iso).timestamp())
    except (ValueError, TypeError):
        raise ValidationError("日付の形式が不正です。")


# ---- ルートロジック（ブログ） ----------------------------------------------

def _create_post(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    svc = _auth_service()
    now_iso, now_epoch = _now()
    profile = svc.get_postable_profile(principal, now_iso=now_iso)
    data = validate(PostInput, parse_body(event.get("body")))
    return _content.create_post(
        author_id=principal.sub, author_display_name=profile.display_name or "",
        data=data, now_iso=now_iso, now_epoch=now_epoch,
    )


def _list_posts_admin(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _content.list_posts_admin(principal, status=_query_param(event, "status"), start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_post_admin(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    return _content.get_post_admin(principal, _path_param(event, "id"))


def _update_post(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, now_epoch = _now()
    data = validate(PostInput, parse_body(event.get("body")))
    return _content.update_post(principal, _path_param(event, "id"), data, now_iso=now_iso, now_epoch=now_epoch)


def _delete_post(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    _content.delete_post(principal, _path_param(event, "id"))
    return {"deleted": True}


def _set_post_status(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, now_epoch = _now()
    body = validate(StatusUpdate, parse_body(event.get("body")))
    return _content.set_post_status(principal, _path_param(event, "id"), body.status, now_iso=now_iso, now_epoch=now_epoch)


# ---- ルートロジック（お知らせ） --------------------------------------------

def _create_notice(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    svc = _auth_service()
    now_iso, now_epoch = _now()
    profile = svc.get_postable_profile(principal, now_iso=now_iso)
    data = validate(NoticeInput, parse_body(event.get("body")))
    return _content.create_notice(
        author_id=principal.sub, author_display_name=profile.display_name or "",
        data=data, now_iso=now_iso, now_epoch=now_epoch,
    )


def _list_notices_admin(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _content.list_notices_admin(principal, status=_query_param(event, "status"), start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_notice_admin(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    return _content.get_notice_admin(principal, _path_param(event, "id"))


def _update_notice(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, now_epoch = _now()
    data = validate(NoticeInput, parse_body(event.get("body")))
    return _content.update_notice(principal, _path_param(event, "id"), data, now_iso=now_iso, now_epoch=now_epoch)


def _delete_notice(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    _content.delete_notice(principal, _path_param(event, "id"))
    return {"deleted": True}


def _set_notice_status(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, now_epoch = _now()
    body = validate(StatusUpdate, parse_body(event.get("body")))
    return _content.set_notice_status(principal, _path_param(event, "id"), body.status, now_iso=now_iso, now_epoch=now_epoch)


# ---- ルートロジック（カレンダー, 共有編集） --------------------------------

def _create_event(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, _ = _now()
    data = validate(EventInput, parse_body(event.get("body")))
    return _calendar.create_event(principal, data, event_date_epoch=_event_date_epoch(data.event_date), now_iso=now_iso)


def _list_events_admin(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    cursor = _decode_cursor(_query_param(event, "cursor"))
    result = _calendar.list_events_admin(status=_query_param(event, "status"), start_key=cursor)
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _update_event(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    now_iso, _ = _now()
    data = validate(EventInput, parse_body(event.get("body")))
    return _calendar.update_event(principal, _path_param(event, "id"), data, event_date_epoch=_event_date_epoch(data.event_date), now_iso=now_iso)


def _delete_event(event, principal):
    auth.require_role(principal, ROLE_ADMIN, ROLE_EDITOR)
    _calendar.delete_event(principal, _path_param(event, "id"))
    return {"deleted": True}


# ---- ルートロジック（問い合わせ, Admin のみ） ------------------------------

def _list_inquiries(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    result = _contact.list_inquiries(status=_query_param(event, "status"))
    return {"items": result["items"], "next_cursor": _encode_cursor(result["next_cursor"])}


def _get_inquiry(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    return _contact.get_inquiry(_path_param(event, "id"))


def _update_inquiry_status(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    now_iso, _ = _now()
    body = validate(InquiryStatusUpdate, parse_body(event.get("body")))
    return _contact.update_inquiry_status(principal, _path_param(event, "id"), body.status, now_iso=now_iso)


# ---- ルートロジック（ユーザー / 自プロフィール） --------------------------

def _invite_editor(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    now_iso, _ = _now()
    body = validate(InviteRequest, parse_body(event.get("body")))
    return _auth_service().invite_editor(principal, str(body.email), now_iso=now_iso)


def _list_users(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    return _auth_service().list_users()


def _set_user_status(event, principal):
    auth.require_role(principal, ROLE_ADMIN)
    now_iso, _ = _now()
    body = validate(SetUserStatusRequest, parse_body(event.get("body")))
    return _auth_service().set_user_status(principal, _path_param(event, "id"), body.status, now_iso=now_iso)


def _complete_profile(event, principal):
    # 認証済みなら誰でも自分のプロフィールを設定可（ロール不問）。
    now_iso, _ = _now()
    body = validate(CompleteProfileRequest, parse_body(event.get("body")))
    return _auth_service().complete_profile(principal, body.display_name, now_iso=now_iso)


# ---- ルーティング表 --------------------------------------------------------

_ROUTES = {
    # ブログ
    "POST /admin/posts": (_create_post, 201),
    "GET /admin/posts": (_list_posts_admin, 200),
    "GET /admin/posts/{id}": (_get_post_admin, 200),
    "PUT /admin/posts/{id}": (_update_post, 200),
    "DELETE /admin/posts/{id}": (_delete_post, 200),
    "PUT /admin/posts/{id}/status": (_set_post_status, 200),
    # お知らせ
    "POST /admin/notices": (_create_notice, 201),
    "GET /admin/notices": (_list_notices_admin, 200),
    "GET /admin/notices/{id}": (_get_notice_admin, 200),
    "PUT /admin/notices/{id}": (_update_notice, 200),
    "DELETE /admin/notices/{id}": (_delete_notice, 200),
    "PUT /admin/notices/{id}/status": (_set_notice_status, 200),
    # カレンダー
    "POST /admin/events": (_create_event, 201),
    "GET /admin/events": (_list_events_admin, 200),
    "PUT /admin/events/{id}": (_update_event, 200),
    "DELETE /admin/events/{id}": (_delete_event, 200),
    # 問い合わせ（Admin）
    "GET /admin/inquiries": (_list_inquiries, 200),
    "GET /admin/inquiries/{id}": (_get_inquiry, 200),
    "PUT /admin/inquiries/{id}/status": (_update_inquiry_status, 200),
    # ユーザー / 自プロフィール
    "POST /admin/users/invite": (_invite_editor, 201),
    "GET /admin/users": (_list_users, 200),
    "PUT /admin/users/{id}/status": (_set_user_status, 200),
    "PUT /admin/me/profile": (_complete_profile, 200),
}


@with_error_handling
def handler(event: dict, context: object) -> dict:
    """Lambda エントリポイント。認証必須 → routeKey ディスパッチ。"""
    principal = auth.require_authenticated(event)   # 未認証は 401（deny-by-default）
    route = _route_key(event)
    origin = _origin(event)
    entry = _ROUTES.get(route)
    if entry is None:
        raise NotFoundError("ルートが見つかりません。")
    func, success_status = entry
    body = func(event, principal)
    logger.info(
        "admin request handled",
        extra={"route": route, "status_code": success_status, "actor": principal.sub},
    )
    return make_response(success_status, body, origin)
