# Code Generation 計画 — U4 blog-migration（IYフレンズ / Phase 1）

現行サイトの既存ブログ（約339件）を新DB（U3 の Posts テーブル）へ移行するバッチを生成する。
**この計画がCode Generationの唯一の正**とする。

---

## 1. ユニットコンテキスト
- **配置（ワークスペース直下）**: `iyf-backend-api/migration/`（U3 に同梱）
- **ドキュメント**: `aidlc-docs/construction/u4-blog-migration/code/`
- **パイプライン**: `scrapeSource(baseUrl) → normalize(記事整形/画像除外) → importPosts → ContentService/Repository → DynamoDB(Posts)` → `ImportReport(件数/重複/失敗)`
- **依存**: U3（content モデル・Posts リポジトリを再利用）
- **ストーリー**: US-06（既存ブログ移行閲覧）
- **方針**: 一度きり/再実行可（冪等）、画像は当面除外（Q14）、fail-closed・構造化ログ・PII非出力

## 2. 設計上の前提（重要）
実サイトのHTML構造は未確定のため、**サイトアダプタ方式**（URL・CSSセレクタを設定で差し替え）で実装し、
- **ドライラン**（DB投入せず件数/正規化結果を確認）
- **サンプルHTMLフィクスチャによるテスト**
を用意する。実セレクタ/URLは実行前に設定ファイルへ記入する。

---

# 確認質問（回答をお願いします）
AI推奨はすべて **A**。「**推奨で**」で一括Aにできます。

## Q-M1: 移行元サイトの状態
現行のブログはどこにありますか？

A) **現行サイトはまだ公開中でスクレイピング可能**（URL/セレクタは後で設定ファイルに記入）（AI推奨・アダプタ方式で汎用実装）

B) 現行サイトは閉鎖済み。HTMLエクスポート/アーカイブ（zip等）がある → そこから取り込む方式にする

C) おまかせ

X) Other（自由記述：サービス名やURLなど分かれば）

[Answer]: 

## Q-M2: 重複判定キー（再実行時の冪等性）
同じ記事を二重に入れないための判定は？

A) **元記事のURL（source_url）で一意判定**（AI推奨・最も確実）

B) タイトル＋投稿日で判定

C) おまかせ

X) Other

[Answer]: 

## Q-M3: 実行方式
移行バッチをどう動かすか？

A) **ローカル実行スクリプト**（PCから AWS 認証情報で直接 DynamoDB に投入）。一度きりに最適・最簡（AI推奨）

B) Lambda 化して実行

C) おまかせ

X) Other

[Answer]: 

## Q-M4: 投入時の公開状態
移行した記事の公開状態は？

A) **published（公開）として投入**（既存記事は公開済みのため、そのまま閲覧可能に）（AI推奨）

B) draft（下書き）で投入し、確認後にまとめて公開

C) おまかせ

X) Other

[Answer]: 

---

## 回答（「推奨で」により全てA採用）
- Q-M1 = A（現行サイト公開中・アダプタ方式でスクレイピング。URL/セレクタは config に記入）
- Q-M2 = A（source_url で重複判定。post_id を source_url の決定的ハッシュにして冪等化）
- Q-M3 = A（ローカル実行スクリプト）
- Q-M4 = A（published として投入、source=migrated）

## 3. 生成ステップ（回答後・番号順）
### Step 1: 構成
- [x] `iyf-backend-api/migration/` 骨組み、`config.example.toml`（baseUrl/セレクタ/認証プロファイル）、README

### Step 2: スクレイパ（アダプタ方式）
- [x] `migration/scraper.py`（`scrape_source(config) -> list[RawPost]`。HTML取得＋セレクタ抽出。robots/礼儀としてレート制御）

### Step 3: 正規化
- [x] `migration/normalize.py`（`normalize(RawPost) -> PostInput`：タイトル/本文サニタイズ/投稿日パース(JST)/著者表示名、画像除外）

### Step 4: 取り込み（冪等）
- [x] `migration/importer.py`（`import_posts(list[PostInput]) -> ImportReport`：source_url 重複回避、Posts へ PutItem、published 投入、source=migrated）

### Step 5: エントリポイント / ドライラン
- [x] `migration/run.py`（`--dry-run` / `--limit` / `--config` 対応、ImportReport 出力）

### Step 6: テスト
- [x] `tests/migration/`（正規化・重複回避・ドライランをサンプルHTMLフィクスチャで検証）

### Step 7: ドキュメント / 要約
- [x] `migration/README.md`（設定・実行手順・ドライラン）
- [x] `aidlc-docs/construction/u4-blog-migration/code/code-generation-summary.md`

## 4. セキュリティ適合
SECURITY-03（PII非出力ログ）/05（正規化時サニタイズ）/06（最小権限：Posts 書き込みのみ）/15（fail-closed・失敗記録）/10（依存固定, U3のロックを共有）。

## 5. トレーサビリティ
US-06。設計参照: `inception/application-design/{components,component-methods,services}.md`、U3 の content モデル/リポジトリ。総ステップ数: 7。
