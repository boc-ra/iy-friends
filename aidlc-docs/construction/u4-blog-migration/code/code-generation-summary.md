# Code Generation Summary — U4 blog-migration（Phase 1）

生成場所: `iyf-backend-api/migration/`（U3 に同梱）。ストーリー US-06。

## 回答（推奨・全A）
Q-M1=A（現行サイトをアダプタ方式でスクレイピング）/ Q-M2=A（source_url で冪等）/ Q-M3=A（ローカルスクリプト）/ Q-M4=A（published 投入）。

## 生成ファイル
| ファイル | 役割 |
|---|---|
| `migration/config.example.toml` | 移行設定サンプル（URL/CSSセレクタ/投入先） |
| `migration/scraper.py` | 現行サイト収集（requests+bs4、アダプタ＝CSSセレクタ、レート制御） |
| `migration/normalize.py` | 正規化（HTML除去/画像除外/日付パース/著者）＝純粋関数中心 |
| `migration/importer.py` | 冪等取り込み（source_url ハッシュで post_id、published、source=migrated）＋ ImportReport |
| `migration/run.py` | CLI（`--config` `--dry-run` `--limit`） |
| `migration/README.md` | 手順・設定・注意 |
| `tests/test_migration.py` | 正規化・冪等・ドライランのテスト |

## U3 への軽微な変更
- `src/content/models.py` の `Post` に `source_url: str | None = None` を追加（移行の冪等/トレーサビリティ用、任意項目・後方互換）。

## 検証
- **pytest: 33 passed**（U3の24＋移行9）。
- 冪等性テスト: 同一入力の再実行で imported=0 / skipped_duplicate=n。
- ドライランは保存しないことを確認。

## セキュリティ適合
SECURITY-03（PII非出力ログ）/05（サニタイズ）/06（Posts書き込みのみ最小権限）/15（fail-closed・失敗集計）/10（依存はU3ロック共有＋移行時のみrequests/bs4）。

## 運用メモ（実行前に必要）
- 現行サイトの実URLと**CSSセレクタを `config.toml` に設定**（実HTML構造依存）。
- `pip install requests beautifulsoup4`、`aws configure` 済みで本投入。
- まず `--dry-run` で件数/正規化を確認 → 本投入。
