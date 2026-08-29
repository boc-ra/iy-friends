"""admin ハンドラ: 認証/認可ガードとルーティング。"""
from __future__ import annotations

import json

from src.handlers import admin


def _event(route, *, sub=None, groups=None, body=None, path_id=None):
    ev = {"routeKey": route, "headers": {}}
    if sub is not None:
        ev["requestContext"] = {"authorizer": {"jwt": {"claims": {
            "sub": sub, "cognito:groups": groups or [],
        }}}}
    else:
        ev["requestContext"] = {}
    if body is not None:
        ev["body"] = json.dumps(body)
    if path_id is not None:
        ev["pathParameters"] = {"id": path_id}
    return ev


def _status(resp):
    return resp["statusCode"]


def test_unauthenticated_401():
    resp = admin.handler(_event("GET /admin/posts"), None)
    assert _status(resp) == 401


def test_unknown_route_404():
    resp = admin.handler(_event("GET /admin/nope", sub="u1", groups=["admin"]), None)
    assert _status(resp) == 404


def test_editor_invite_forbidden_403():
    # 招待は Admin のみ。editor は 403（Cognito に触れる前に拒否）。
    resp = admin.handler(
        _event("POST /admin/users/invite", sub="ed1", groups=["editor"], body={"email": "x@y.com"}),
        None,
    )
    assert _status(resp) == 403


def test_editor_list_inquiries_forbidden_403():
    resp = admin.handler(_event("GET /admin/inquiries", sub="ed1", groups=["editor"]), None)
    assert _status(resp) == 403


def test_list_posts_admin_ok(monkeypatch):
    class _FakeContent:
        def list_posts_admin(self, principal, *, status=None, start_key=None):
            return {"items": [{"post_id": "p1", "status": "draft"}], "next_cursor": None}

    monkeypatch.setattr(admin, "_content", _FakeContent())
    resp = admin.handler(_event("GET /admin/posts", sub="ad1", groups=["admin"]), None)
    assert _status(resp) == 200
    body = json.loads(resp["body"])
    assert body["items"][0]["post_id"] == "p1"


def test_no_role_group_forbidden_403(monkeypatch):
    # グループ無し（role 空）は deny-by-default で 403。
    resp = admin.handler(_event("GET /admin/posts", sub="u1", groups=[]), None)
    assert _status(resp) == 403
