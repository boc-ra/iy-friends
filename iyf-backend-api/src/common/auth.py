"""認可（SECURITY-08 / SECURITY-12）。Phase 2 本実装。

責務分担（NFR-U3-AUTH-06 / nfr-design-patterns-phase2 §1.1）:
- 層1（API Gateway JWT オーソライザ）: 署名・失効・iss・aud・exp を検証済み。
- 層2（本モジュール）: 検証済み claim から Principal を復元し、
  ロール認可（require_role）とオーナー認可（require_owner, IDOR 防止）を行う。

deny-by-default: 未認証は 401、権限不足/他人リソースは 403（fail-closed）。
判定ロジックは純粋関数（`is_role_allowed` / `is_owner_allowed`）に分離し PBT 可能とする。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.common.errors import ForbiddenError, UnauthorizedError

# ロール定数（Cognito グループ名と一致）。
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"


@dataclass(frozen=True)
class Principal:
    """認証済み呼び出し元。JWT claim 由来・非永続。"""

    sub: str
    role: str
    groups: tuple[str, ...] = field(default_factory=tuple)

    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


# ---- claim 復元 -------------------------------------------------------------

def _extract_claims(event: dict) -> dict:
    ctx = event.get("requestContext", {}) if isinstance(event, dict) else {}
    authorizer = ctx.get("authorizer", {}) or {}
    jwt = authorizer.get("jwt", {}) or {}
    return jwt.get("claims", {}) or {}


def _normalize_groups(raw) -> tuple[str, ...]:
    """cognito:groups は文字列/リスト/カンマ区切りのいずれもあり得る。"""
    if raw is None:
        return ()
    if isinstance(raw, (list, tuple)):
        return tuple(str(g) for g in raw if g)
    text = str(raw).strip().strip("[]")
    if not text:
        return ()
    parts = [p.strip() for p in text.replace(",", " ").split()]
    return tuple(p for p in parts if p)


def _role_from_groups(groups: tuple[str, ...]) -> str:
    """admin を優先し、なければ editor、いずれも無ければ空（=権限なし）。"""
    if ROLE_ADMIN in groups:
        return ROLE_ADMIN
    if ROLE_EDITOR in groups:
        return ROLE_EDITOR
    return ""


def get_principal(event: dict) -> Principal | None:
    """検証済み JWT claim から Principal を復元。未認証は None。"""
    claims = _extract_claims(event)
    sub = claims.get("sub")
    if not sub:
        return None
    groups = _normalize_groups(claims.get("cognito:groups"))
    role = _role_from_groups(groups)
    return Principal(sub=str(sub), role=role, groups=groups)


# ---- 純粋判定関数（PBT 対象） ----------------------------------------------

def is_role_allowed(role: str, allowed: tuple[str, ...]) -> bool:
    """role が許可集合に含まれるか（空ロールは常に不許可, deny-by-default）。"""
    if not role:
        return False
    return role in allowed


def is_owner_allowed(role: str, actor_sub: str, resource_author_id: str | None) -> bool:
    """admin は常に許可。editor は自分が作成者のときのみ許可（IDOR 防止）。"""
    if role == ROLE_ADMIN:
        return True
    if not resource_author_id:
        # 作成者不明のリソースへの editor アクセスは拒否（fail-closed）。
        return False
    return actor_sub == resource_author_id


# ---- ガード（副作用: 例外送出） --------------------------------------------

def require_authenticated(event: dict) -> Principal:
    """認証必須。未認証は 401。"""
    principal = get_principal(event)
    if principal is None:
        raise UnauthorizedError()
    return principal


def require_role(principal: Principal, *allowed: str) -> None:
    """ロール認可。許可外は 403。"""
    if not is_role_allowed(principal.role, allowed):
        raise ForbiddenError()


def require_owner(principal: Principal, resource_author_id: str | None) -> None:
    """オーナー認可（IDOR 防止）。admin 素通り / editor は自リソースのみ。"""
    if not is_owner_allowed(principal.role, principal.sub, resource_author_id):
        raise ForbiddenError()


# ---- 公開エンドポイント用（Phase 1 互換） ----------------------------------

def require_public() -> None:
    """公開エンドポイントの通過点（明示のためのノーオペ）。"""
    return None
