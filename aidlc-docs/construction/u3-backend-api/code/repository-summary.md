# リポジトリ レイヤ 要約

DynamoDB アクセス（各モジュール `repository.py`、`common/db.py` 基底）。パラメータ化・Scan回避・最小権限。

| リポジトリ | テーブル | 主操作 | インデックス |
|---|---|---|---|
| PostRepository / NoticeRepository | Posts / Notices | get / list_published | GSI-published（gsi_status, published_at_epoch↓） |
| EventRepository | Events | get / list_published(昇順) | GSI-date（gsi_status, event_date_epoch↑） |
| InquiryRepository | Inquiries | save / update_notified / find_recent_duplicate | GSI-dedup（dedup_key, created_at_epoch） |

- モデル⇔item 変換（`*_to_item` / `item_to_*`）はPBTでシリアライズ往復を検証。
- 公開GSIは published のときのみ `gsi_status="published"` を付与し、draft を一覧から除外。
テスト: 各 `test_*.py` にフェイクリポジトリで検証（Build&Test で moto 実結合を実施予定）。
