# blog-migration（U4）— 既存ブログ移行バッチ

現行サイトの既存ブログ記事（約339件）を新DB（`Posts` テーブル）へ取り込むローカルバッチ。
一度きり〜再実行可能（冪等）。写真は当面除外（Q14）。

## 仕組み
```
scrape_source(現行サイト, アダプタ=CSSセレクタ)
  → normalize(タイトル/本文/投稿日/著者, 画像除外)
  → import_posts(source_url で冪等, published 投入, source=migrated)
  → ImportReport(件数/重複/失敗)
```
- **冪等キー**: `post_id = "mig-" + sha256(source_url)`（Q-M2=A）。再実行しても重複投入しない。
- **公開状態**: published（Q-M4=A）。

## セットアップ
```bash
# 追加依存（移行時のみ）
pip install requests beautifulsoup4
# 設定
cp migration/config.example.toml migration/config.toml
# → config.toml を現行サイトのURL/CSSセレクタに合わせて編集
```

## 実行
```bash
# まずドライラン（DB投入せず件数・正規化を確認）
python -m migration.run --config migration/config.toml --dry-run --limit 5

# 問題なければ本投入（AWS認証情報が必要: aws configure 済みであること）
python -m migration.run --config migration/config.toml
```
出力は ImportReport（imported / skipped_duplicate / failed / warnings）をJSONで表示。

## 設定のポイント（config.toml）
- `[source] list_url`：記事一覧URL（ページングは `{page}`）
- `[selectors]`：一覧リンク・タイトル・本文・日付・著者の CSS セレクタ（実サイトに合わせる）
- `[normalize] exclude_images`：true で画像除外
- `[import] table_posts`：投入先テーブル（例 `iyf-prod-Posts`）

## セキュリティ
- 本文/タイトルはサニタイズ（SECURITY-05）、ログにPIIを出さない（SECURITY-03）
- IAM は Posts への書き込み権限のみ（最小権限, SECURITY-06）
- 失敗は fail-closed で件数記録し継続、詳細はログ（SECURITY-15）

## 注意
- 実サイトのHTML構造に依存するため、`config.toml` の CSS セレクタ調整が必要。
- スクレイピングは自クラブの現行サイトが対象（許諾の範囲内）。負荷配慮のため `request_delay_seconds` を設定。
