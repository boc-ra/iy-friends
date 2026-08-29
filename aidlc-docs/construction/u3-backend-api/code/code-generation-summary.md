# Code Generation Summary — U3 backend-api（Phase 1）

生成場所: ワークスペース直下 `iyf-backend-api/`（ポリレポ）。ドキュメントは本 `code/` 配下（Markdown要約のみ）。

## 生成ファイル一覧（アプリコード）

### 共通基盤 common（Step 2）
- `src/common/config.py` — 環境変数＋SSM(SecureString)設定、JST、テーブル名、ページサイズ、CORS
- `src/common/logging.py` — 構造化JSONログ・相関ID・PIIマスク（SECURITY-03）
- `src/common/errors.py` — 例外型・`with_error_handling`（グローバル・fail-closed）・`make_response`（CORS/セキュリティヘッダ）（SECURITY-15/09/08/04）
- `src/common/validation.py` — `parse_body`/`validate`（Pydantic）/`sanitize_text`/`clamp_limit`（SECURITY-05）
- `src/common/auth.py` — 認可前段（公開/認証判定、Cognito claim 復元）（SECURITY-08）
- `src/common/db.py` — DynamoDB リポジトリ基底（Query/GetItem/PutItem、限定リトライ、Scan回避）（SECURITY-06）
- `src/common/audit.py` — 監査ログ（SECURITY-13）

### ビジネスロジック / リポジトリ（Step 5, 8）
- `src/content/{models,repository,service}.py` — Post/Notice、公開一覧/詳細（US-01/04/05/06/08）
- `src/calendar/{models,repository,service}.py` — Event、日付順一覧/詳細（US-10）
- `src/contact/{models,repository,notifier,service}.py` — Inquiry、受付＋軽量冪等＋SES同期通知（US-13）

### APIレイヤ（Step 11）
- `src/handlers/public.py` — routeKey ディスパッチ、検証→認可→サービス→エラー整形、カーソルページング

### デプロイ / 設定（Step 1, 15）
- `pyproject.toml` / `requirements.txt`（依存固定, SECURITY-10）/ `.gitignore`
- `template.yaml`（SAM: HTTP API＋スロットリング＋アクセスログ、Lambda arm64、DynamoDB×5[On-Demand/PITR/SSE/GSI]、最小権限IAM、LogGroup保持90日）
- `samconfig.toml`（prod, ap-northeast-1）
- `README.md`

### テスト（Step 3, 6, 9, 12）
- `tests/test_common.py` `test_content.py` `test_calendar.py` `test_contact.py` `test_handlers.py`
- **結果: 24 passed**（PBT含む）。PBT が `clamp_limit` の上限未丸めバグを検出→修正済み。

## ストーリー対応（Phase 1）
| ストーリー | 実装 |
|---|---|
| US-01/04/05 ブログ | content（一覧/詳細、公開フィルタ、10件ページング） |
| US-06 移行ブログ配信 | content（source=migrated も同一配信。データ投入はU4） |
| US-08 お知らせ | content（Notice） |
| US-10 カレンダー | calendar（日付昇順） |
| US-13 問い合わせ送信 | contact（保存＋SES＋軽量冪等） |
| US-18 セキュリティ横断 | common 全般＋SAM |
| US-19 低コスト運用 | サーバーレス最小構成（arm64/On-Demand/単一リージョン/prod単独） |

## セキュリティ適合（コード層）
SECURITY-03/05/06/08/09/11(前提)/13/15 をコードで実装、SECURITY-10 を依存固定/CIで。
SECURITY-12（認証本体）は Phase 2 の auth 実装で完成。SECURITY-02/04(HTML)/07 はインフラ/U5。

## Phase 2 先送り（未実装）
管理系書き込み（US-07/09/11/14）、ログイン・招待（US-15/16、`src/auth/`）、`migration/`（U4）。
