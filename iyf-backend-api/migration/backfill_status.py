"""GSI-status バックフィル（Phase 2）。

Posts / Notices の既存レコードに `updated_at_epoch` を補完する。
Phase 2 で追加した `GSI-status`（PK=status, SK=updated_at_epoch）へ既存レコードを
掲載するために必要（`status` は既存 item に常時設定済みだが、updated_at_epoch は無い）。

- Events / Inquiries は SK に既存属性（event_date_epoch / created_at_epoch）を用いるため
  バックフィル不要（`status` も常時設定済み）。
- 冪等: `updated_at_epoch` が既にあるレコードはスキップ。
- 値: `published_at_epoch` があればそれを、無ければ `--default-epoch`（既定 0）を設定。

使い方:
  python -m migration.backfill_status --dry-run
  python -m migration.backfill_status
  python -m migration.backfill_status --default-epoch 1700000000
"""
from __future__ import annotations

import argparse
import json
import sys

from src.common.config import TABLE_NOTICES, TABLE_POSTS
from src.common.db import Repository
from src.common.logging import get_logger

logger = get_logger("iyf.migration.backfill")


def _backfill_table(table_name: str, pk_name: str, *, default_epoch: int, dry_run: bool) -> dict:
    repo = Repository(table_name)
    items = repo.scan_all()
    scanned = len(items)
    updated = 0
    skipped = 0
    for item in items:
        if item.get("updated_at_epoch") is not None:
            skipped += 1
            continue
        epoch = item.get("published_at_epoch")
        if epoch is None:
            epoch = default_epoch
        if not dry_run:
            repo.update_item({pk_name: item[pk_name]}, {"updated_at_epoch": int(epoch)})
        updated += 1
    return {"table": table_name, "scanned": scanned, "updated": updated, "skipped": skipped}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GSI-status バックフィル（Posts/Notices）")
    parser.add_argument("--dry-run", action="store_true", help="更新せず件数のみ確認")
    parser.add_argument("--default-epoch", type=int, default=0,
                        help="published_at_epoch が無いレコードに設定する updated_at_epoch")
    args = parser.parse_args(argv)

    reports = [
        _backfill_table(TABLE_POSTS, "post_id", default_epoch=args.default_epoch, dry_run=args.dry_run),
        _backfill_table(TABLE_NOTICES, "notice_id", default_epoch=args.default_epoch, dry_run=args.dry_run),
    ]
    result = {"dry_run": args.dry_run, "tables": reports}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    logger.info("backfill done", extra={"event": result})
    return 0


if __name__ == "__main__":
    sys.exit(main())
