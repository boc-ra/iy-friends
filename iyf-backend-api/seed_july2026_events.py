"""2026年7月の活動予定をカレンダー(Events)へ一括投入する（試し用シード）。

実行方法（iyf-backend-api ディレクトリで、venv 有効・AWS_PROFILE=iyf・SSOログイン済み）:
  $env:AWS_PROFILE = "iyf"
  $env:TABLE_EVENTS = "iyf-prod-Events"
  python seed_july2026_events.py            # 投入（既存に追加）
  python seed_july2026_events.py --reset    # 既存の予定を全削除してから14件を投入（重複解消・推奨）
  python seed_july2026_events.py --dry-run  # 確認のみ（DBに書かない）

- 公開状態(published)で投入するため、投入後すぐ公開サイトのカレンダーに表示されます。
- 鍵当番の氏名は公開サイトには載せません（個人情報最小化）。
- --reset は Events テーブルの**全予定を削除**してから入れ直します（試しデータ前提）。
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

os.environ.setdefault("TABLE_EVENTS", "iyf-prod-Events")
os.environ.setdefault("AWS_REGION", "ap-northeast-1")

JST = timezone(timedelta(hours=9))

# (日, 開始時, 開始分, タイトル, 時間帯表記, 連絡事項)
# 休みは (日, None, None, "休み", "", 説明) とする。
ENTRIES = [
    (2,  18, 45, "練習",          "18:45〜21:00", ""),
    (4,  None, None, "休み",       "",             "お休みです。"),
    (5,   9,  0, "練習（1日練習）", "9:00〜15:00",  "1日練習です。お弁当をご用意ください。"),
    (9,  18, 45, "練習",          "18:45〜21:00", "部費袋を配布します。"),
    (11, 17,  0, "練習",          "17:00〜19:00", ""),
    (12,  9,  0, "練習・保護者会",  "9:00〜13:00",  "保護者会（夏祭り＆合宿説明会）を行います。"),
    (16, 18, 45, "練習",          "18:45〜21:00", "部費を回収します。"),
    (18, None, None, "休み",       "",             "お休みです（第三土曜日は原則休み／他団体利用のため）。"),
    (19,  9,  0, "練習",          "9:00〜13:00",  ""),
    (20,  9,  0, "練習（仮・1日練習）", "9:00〜15:00", "1日練習（仮）です。お弁当をご用意ください。※日程は仮です。"),
    (23, 18, 45, "練習",          "18:45〜21:00", ""),
    (25, 17,  0, "練習",          "17:00〜19:00", ""),
    (26,  9,  0, "練習・保護者会",  "9:00〜13:00",  "保護者会（夏祭り＆合宿説明会）を行います。"),
    (30, 18, 45, "練習",          "18:45〜21:00", ""),
]

LOCATION = "上郷小学校"


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    dry = "--dry-run" in args
    reset = "--reset" in args

    # 依存（boto3・アプリモデル）を読み込む。
    from src.calendar.models import Event, EventStatus
    from src.calendar.repository import EventRepository

    repo = None if dry else EventRepository()

    # --reset: 既存の予定を全削除（重複解消）。
    if reset and not dry:
        existing = repo.scan_all()
        for it in existing:
            repo.delete({"event_id": it["event_id"]})
        print(f"既存 {len(existing)} 件を削除しました。")
    elif reset and dry:
        print("[dry-run] --reset 指定（実行時は既存の全予定を削除します）")
    count = 0
    for day, hh, mm, title, timespan, note in ENTRIES:
        # 休みは 0:00、練習は開始時刻。
        h, m = (0, 0) if hh is None else (hh, mm)
        dt = datetime(2026, 7, day, h, m, tzinfo=JST)
        parts = [p for p in (timespan, note) if p]
        description = "／".join(parts)
        ev = Event(
            event_id=str(uuid.uuid4()),
            title=title,
            description=description,
            location=("" if title == "休み" else LOCATION),
            event_date=dt.isoformat(),
            event_date_epoch=int(dt.timestamp()),
            status=EventStatus.PUBLISHED,
        )
        print(f"{dt.date()} {title:12} {ev.location:6} {description}")
        if not dry:
            repo.save(ev)
        count += 1

    print(f"\n{'[dry-run] ' if dry else ''}{count} 件の予定を{'確認' if dry else '投入'}しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
