"""監査ログ（SECURITY-13）。

重要データ変更（投稿の公開状態、問い合わせ状態遷移など）を
actor / timestamp / before-after 付きで記録する。Phase 1 では構造化ログへ出力し、
Phase 2 で改ざん耐性ストア（追記専用）への転送を検討する。
"""
from __future__ import annotations

from src.common.logging import get_logger

logger = get_logger("iyf.audit")


def record_change(
    *,
    entity: str,
    entity_id: str,
    action: str,
    actor: str,
    before: object = None,
    after: object = None,
) -> None:
    """重要データ変更を監査記録する。PII は含めない（要約のみ）。"""
    logger.info(
        "audit",
        extra={
            "event": {
                "entity": entity,
                "entity_id": entity_id,
                "action": action,
                "actor": actor,
                "before": before,
                "after": after,
            }
        },
    )
