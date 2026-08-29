"""移行エントリポイント（ローカル実行, Q-M3=A）。

使い方:
  python -m migration.run --config migration/config.toml --dry-run
  python -m migration.run --config migration/config.toml --limit 5
  python -m migration.run --config migration/config.toml           # 本投入

--dry-run: DB へ投入せず、収集・正規化・件数のみ確認。
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib

from migration.importer import import_posts
from migration.normalize import normalize
from migration.scraper import scrape_source
from src.common.logging import get_logger

logger = get_logger("iyf.migration")


def load_config(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _build_repo(config: dict):
    """Posts リポジトリを構築（本投入時のみ AWS 接続）。"""
    import os

    table = config.get("import", {}).get("table_posts")
    if table:
        os.environ.setdefault("TABLE_POSTS", table)
    region = config.get("import", {}).get("aws_region")
    if region:
        os.environ.setdefault("AWS_REGION", region)
    from src.content.repository import PostRepository

    return PostRepository()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IYフレンズ 既存ブログ移行バッチ")
    parser.add_argument("--config", required=True, help="設定ファイル(TOML)")
    parser.add_argument("--dry-run", action="store_true", help="DB投入せず確認のみ")
    parser.add_argument("--limit", type=int, default=None, help="処理件数の上限")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    norm_cfg = config.get("normalize", {})
    default_author = norm_cfg.get("default_author", "IYフレンズ")
    exclude_images = bool(norm_cfg.get("exclude_images", True))
    publish_status = config.get("import", {}).get("publish_status", "published")

    logger.info("scrape start", extra={"event": {"dry_run": args.dry_run, "limit": args.limit}})
    raws = scrape_source(config, limit=args.limit)
    inputs = [normalize(r, default_author=default_author, exclude_images=exclude_images) for r in raws]
    logger.info("normalized", extra={"event": {"count": len(inputs)}})

    if args.dry_run:
        repo = None

        class _NullRepo:
            def get_post(self, _):  # 常に新規扱い（件数見積り）
                return None

        repo = _NullRepo()
        report = import_posts(inputs, repo, publish_status=publish_status, dry_run=True)
    else:
        repo = _build_repo(config)
        report = import_posts(inputs, repo, publish_status=publish_status, dry_run=False)

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    logger.info("done", extra={"event": report.as_dict()})
    # 失敗があれば非0終了（CI/運用で検知しやすく）。
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
