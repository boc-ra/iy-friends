"""auth: 認可判定（純粋関数・PBT）と AuthService（招待/完了/無効化）。"""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.auth.models import ProfileState, Role, UserProfile, UserStatus
from src.auth.service import AuthService
from src.common.auth import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    Principal,
    get_principal,
    is_owner_allowed,
    is_role_allowed,
    require_owner,
    require_role,
)
from src.common.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError


# ---- 純粋判定関数 ----

def test_is_role_allowed_empty_role_denied():
    assert is_role_allowed("", (ROLE_ADMIN, ROLE_EDITOR)) is False


def test_is_role_allowed_match():
    assert is_role_allowed(ROLE_EDITOR, (ROLE_ADMIN, ROLE_EDITOR)) is True
    assert is_role_allowed(ROLE_EDITOR, (ROLE_ADMIN,)) is False


def test_is_owner_allowed_admin_always():
    assert is_owner_allowed(ROLE_ADMIN, "u1", "other") is True


def test_is_owner_allowed_editor_self_only():
    assert is_owner_allowed(ROLE_EDITOR, "u1", "u1") is True
    assert is_owner_allowed(ROLE_EDITOR, "u1", "u2") is False
    assert is_owner_allowed(ROLE_EDITOR, "u1", None) is False


@given(actor=st.text(min_size=1, max_size=8), owner=st.text(min_size=1, max_size=8))
def test_owner_pbt_editor_matches_iff_equal(actor, owner):
    assert is_owner_allowed(ROLE_EDITOR, actor, owner) == (actor == owner)
    # admin は所有者に関わらず常に許可。
    assert is_owner_allowed(ROLE_ADMIN, actor, owner) is True


# ---- claim 復元 ----

def _event_with_groups(sub, groups):
    return {"requestContext": {"authorizer": {"jwt": {"claims": {
        "sub": sub, "cognito:groups": groups,
    }}}}}


def test_get_principal_admin_priority():
    p = get_principal(_event_with_groups("u1", ["editor", "admin"]))
    assert p is not None and p.role == ROLE_ADMIN


def test_get_principal_string_group():
    p = get_principal(_event_with_groups("u1", "editor"))
    assert p.role == ROLE_EDITOR


def test_get_principal_unauth():
    assert get_principal({"requestContext": {}}) is None


def test_require_role_and_owner_raise():
    editor = Principal(sub="u1", role=ROLE_EDITOR, groups=("editor",))
    with pytest.raises(ForbiddenError):
        require_role(editor, ROLE_ADMIN)
    with pytest.raises(ForbiddenError):
        require_owner(editor, "someone-else")
    require_role(editor, ROLE_ADMIN, ROLE_EDITOR)   # 例外なし
    require_owner(editor, "u1")                       # 自分 → 例外なし


# ---- AuthService（fake 注入） ----

class _FakeCognito:
    def __init__(self, *, existing_emails=None):
        self.existing = set(existing_emails or [])
        self.created = []
        self.groups = []
        self.disabled = []
        self.enabled = []

    def admin_create_user(self, email):
        if email in self.existing:
            raise ConflictError("既に登録されています。")
        self.existing.add(email)
        self.created.append(email)
        return f"sub-{email}"

    def add_to_group(self, sub, group):
        self.groups.append((sub, group))

    def disable_user(self, username):
        self.disabled.append(username)

    def enable_user(self, username):
        self.enabled.append(username)


class _FakeUserRepo:
    def __init__(self, profiles=None):
        self._by_id = {p.user_id: p for p in (profiles or [])}

    def get(self, user_id):
        return self._by_id.get(user_id)

    def put_profile(self, profile):
        self._by_id[profile.user_id] = profile

    def update_profile_fields(self, user_id, updates):
        p = self._by_id[user_id]
        data = p.model_dump()
        data.update(updates)
        self._by_id[user_id] = UserProfile.model_validate(data)

    def list_all(self):
        return list(self._by_id.values())

    def count_active_admins(self):
        return sum(
            1 for p in self._by_id.values()
            if p.role == Role.ADMIN and p.status == UserStatus.ACTIVE
        )


def _admin_principal(sub="admin1"):
    return Principal(sub=sub, role=ROLE_ADMIN, groups=("admin",))


def test_invite_editor_creates_stub_and_group():
    repo = _FakeUserRepo()
    cog = _FakeCognito()
    svc = AuthService(repo=repo, cognito=cog)
    summary = svc.invite_editor(_admin_principal(), "Coach@Example.com ", now_iso="2026-07-20T09:00:00+09:00")
    assert cog.created == ["coach@example.com"]           # 正規化
    # Cognito は UsernameAttributes=[email] のため、グループ追加も email を Username として使う。
    assert cog.groups == [("coach@example.com", "editor")]
    assert summary["role"] == "editor"
    assert summary["profile_state"] == "pending"


def test_invite_duplicate_conflict():
    svc = AuthService(repo=_FakeUserRepo(), cognito=_FakeCognito(existing_emails={"dup@example.com"}))
    with pytest.raises(ConflictError):
        svc.invite_editor(_admin_principal(), "dup@example.com", now_iso="t")


def test_complete_profile_sets_complete():
    pending = UserProfile(
        user_id="u9", email="e@x.com", role=Role.EDITOR,
        status=UserStatus.ACTIVE, profile_state=ProfileState.PENDING,
    )
    repo = _FakeUserRepo([pending])
    svc = AuthService(repo=repo, cognito=_FakeCognito())
    p = Principal(sub="u9", role=ROLE_EDITOR, groups=("editor",))
    out = svc.complete_profile(p, "コーチ太郎", now_iso="t")
    assert out["display_name"] == "コーチ太郎"
    assert out["profile_state"] == "complete"
    assert repo.get("u9").is_postable() is True


def test_get_postable_profile_pending_conflict():
    pending = UserProfile(
        user_id="u9", email="e@x.com", role=Role.EDITOR,
        status=UserStatus.ACTIVE, profile_state=ProfileState.PENDING,
    )
    svc = AuthService(repo=_FakeUserRepo([pending]), cognito=_FakeCognito())
    p = Principal(sub="u9", role=ROLE_EDITOR, groups=("editor",))
    with pytest.raises(ConflictError):
        svc.get_postable_profile(p, now_iso="t")


def test_set_user_status_self_disable_conflict():
    admin = UserProfile(user_id="admin1", email="a@x.com", role=Role.ADMIN,
                        status=UserStatus.ACTIVE, profile_state=ProfileState.COMPLETE)
    svc = AuthService(repo=_FakeUserRepo([admin]), cognito=_FakeCognito())
    with pytest.raises(ConflictError):
        svc.set_user_status(_admin_principal("admin1"), "admin1", UserStatus.DISABLED, now_iso="t")


def test_set_user_status_last_admin_conflict():
    admin = UserProfile(user_id="admin2", email="a2@x.com", role=Role.ADMIN,
                        status=UserStatus.ACTIVE, profile_state=ProfileState.COMPLETE)
    svc = AuthService(repo=_FakeUserRepo([admin]), cognito=_FakeCognito())
    with pytest.raises(ConflictError):
        svc.set_user_status(_admin_principal("admin1"), "admin2", UserStatus.DISABLED, now_iso="t")


def test_set_user_status_disable_editor_ok():
    editor = UserProfile(user_id="ed1", email="e@x.com", role=Role.EDITOR,
                        status=UserStatus.ACTIVE, profile_state=ProfileState.COMPLETE)
    admin = UserProfile(user_id="admin1", email="a@x.com", role=Role.ADMIN,
                        status=UserStatus.ACTIVE, profile_state=ProfileState.COMPLETE)
    repo = _FakeUserRepo([editor, admin])
    cog = _FakeCognito()
    svc = AuthService(repo=repo, cognito=cog)
    out = svc.set_user_status(_admin_principal("admin1"), "ed1", UserStatus.DISABLED, now_iso="t")
    assert out["status"] == "disabled"
    assert cog.disabled == ["e@x.com"]


def test_set_user_status_not_found():
    svc = AuthService(repo=_FakeUserRepo(), cognito=_FakeCognito())
    with pytest.raises(NotFoundError):
        svc.set_user_status(_admin_principal(), "missing", UserStatus.DISABLED, now_iso="t")
