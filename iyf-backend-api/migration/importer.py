"""取り込み: 正規化済み PostInput を Posts テーブルへ投入。

- 冪等（Q-M2=A）: post_id を source_url の決定的ハッシュにし、既存は skip。
  → 追加のGSIやScan不要で再実行可能。
- 投入は published（Q-M4=A）、source=migrated。
- fail-closed: 1件の失敗で全体を止めず、ImportReport に記録して継続。
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from src.content.models import Post, PublishStatus
from migration.normalize import PostInput


def make_post_id(source_url: str) -> str:
    """source_url から決定的な post_id を生成（冪等キー）。純粋関数。"""
    digest = hashlib.sha256(source_url.strip().encode("utf-8")).hexdigest()[:16]
    return f"mig-{digest}"


@dataclass
class ImportReport:
    imported: int = 0
    skipped_duplicate: int = 0
    failed: int = 0
    failures: list[str] = field(default_factory=list)
    warnings: int = 0

    def as_dict(self) -> dict:
        return {
            "imported": self.imported,
            "skipped_duplicate": self.skipped_duplicate,
            "failed": self.failed,
            "warnings": self.warnings,
            "failures": self.failures,
        }


def to_post(item: PostInput, *, publish_status: str = "published") -> Post:
    """PostInput → Post（移行用）。"""
    status = PublishStatus(publish_status)
    return Post(
        post_id=make_post_id(item.source_url),
        title=item.title,
        body=item.body,
        author_display_name=item.author_display_name,
        status=status,
        published_at=item.published_at_iso or None,
        published_at_epoch=item.published_at_epoch or None,
        source="migrated",
        source_url=item.source_url,
    )


def import_posts(
    inputs: list[PostInput],
    repo,
    *,
    publish_status: str = "published",
    dry_run: bool = False,
) -> ImportReport:
    """PostInput のリストを冪等に投入する。

    repo は `get_post(post_id)` と（dry_runでない場合）モデル保存手段を持つ。
    ここでは repo.get_post と repo.put（item）を利用する。
    """
    from src.content.repository import post_to_item

    report = ImportReport()
    for item in inputs:
        report.warnings += len(item.warnings)
        try:
            post = to_post(item, publish_status=publish_status)
            existing = repo.get_post(post.post_id)
            if existing is not None:
                report.skipped_duplicate += 1
                continue
            if not dry_run:
                repo.put(post_to_item(post))
            report.imported += 1
        except Exception as exc:  # noqa: BLE001 — 1件失敗で継続（fail-safe集計）。
            report.failed += 1
            report.failures.append(f"{item.source_url}: {type(exc).__name__}")
    return report
