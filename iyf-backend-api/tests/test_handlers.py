"""public ハンドラのユニットテスト（ディスパッチ・検証・エラー整形）。"""
from __future__ import annotations

import json

import src.handlers.public as public


def _event(route_key, *, body=None, path=None, query=None, origin=None):
    return {
        "routeKey": route_key,
        "body": body,
        "pathParameters": path or {},
        "queryStringParameters": query or {},
        "headers": {"origin": origin} if origin else {},
        "requestContext": {"requestId": "req-1", "http": {}},
    }


def test_unknown_route_returns_404():
    resp = public.handler(_event("GET /nope"), None)
    assert resp["statusCode"] == 404


def test_contact_validation_error_returns_400(monkeypatch):
    # 不正な body（email 欠落）は 400。
    resp = public.handler(_event("POST /contact", body=json.dumps({"name": "x"})), None)
    assert resp["statusCode"] == 400


def test_contact_success(monkeypatch):
    monkeypatch.setattr(public._contact, "submit", lambda *a, **k: {"status": "accepted", "inquiry_id": "i1"})
    body = json.dumps({"name": "太郎", "email": "t@example.com", "message": "hello"})
    resp = public.handler(_event("POST /contact", body=body), None)
    assert resp["statusCode"] == 201
    assert json.loads(resp["body"])["inquiry_id"] == "i1"


def test_list_posts_success(monkeypatch):
    monkeypatch.setattr(public._content, "list_posts", lambda **k: {"items": [{"post_id": "p1"}], "next_cursor": None})
    resp = public.handler(_event("GET /posts"), None)
    assert resp["statusCode"] == 200
    payload = json.loads(resp["body"])
    assert payload["items"][0]["post_id"] == "p1"
    assert payload["next_cursor"] is None


def test_response_has_security_headers():
    resp = public.handler(_event("GET /nope"), None)
    assert resp["headers"]["X-Content-Type-Options"] == "nosniff"


def test_cors_only_for_allowed_origin(monkeypatch):
    monkeypatch.setattr(public, "_content", public._content)
    # 許可リスト外オリジンには Allow-Origin を付与しない。
    resp = public.handler(_event("GET /nope", origin="https://evil.example"), None)
    assert "Access-Control-Allow-Origin" not in resp["headers"]
