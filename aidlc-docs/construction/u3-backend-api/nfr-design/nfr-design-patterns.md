# NFR Design Patterns — U3 backend-api（IYフレンズ）

NFR要件（`../nfr-requirements/`）と設計回答（Q-D1=A 同期送信 / Q-D2=A 軽量冪等 / Q-D3=A CDN・APIGWキャッシュのみ）を、具体的な設計パターンに落とし込む。
方針: **最安・シンプル・fail-closed**。過剰な回復力・性能投資はしない。

---

## 1. 性能パターン（Performance）

| パターン | 適用 | 対応NFR |
|---|---|---|
| **キャッシュ・アサイド（読み取り）** | 公開GET（記事/お知らせ/イベント一覧・詳細）は CloudFront + API Gateway キャッシュで配信。DAX不使用（Q-D3=A） | NFR-U3-PERF-01, NFR-PERF-02 |
| **キー設計最適化** | DynamoDB は Query/GetItem 中心、Scan回避。一覧は PK/SK ＋必要に応じ GSI（公開・日付順） | NFR-U3-PERF-01 |
| **ページネーション** | 1ページ10件（Q-F6）、LastEvaluatedKey ベースのカーソル方式 | NFR-U3-PERF-01 |
| **ペイロード最小化** | 一覧は要約フィールドのみ返却、詳細は個別取得 | NFR-U3-PERF-01 |

## 2. スケーラビリティパターン（Scalability）

| パターン | 適用 | 対応NFR |
|---|---|---|
| **サーバーレス自動スケール** | Lambda 同時実行（既定枠）、DynamoDB On-Demand。閾値管理・キャパシティ計画なし | NFR-U3-SCALE-01/02 |
| **ステートレス関数** | Lambda はステートレス。状態は DynamoDB / Cognito に外部化 | NFR-U3-SCALE-01 |

## 3. 回復力・信頼性パターン（Resilience / Reliability）

| パターン | 適用 | 対応NFR |
|---|---|---|
| **DB先行保存（Write-first）＋ベストエフォート通知** | 問い合わせは (1) DynamoDB保存を成立させてから (2) SES同期送信。SES失敗はエラーにせずログ＋ステータス記録し、管理画面で確認可（Q-D1=A） | NFR-U3-REL-01, BR-CONTACT |
| **限定リトライ（bounded retry）** | DynamoDB/SES/Cognito 呼び出しは boto3 標準リトライ（指数バックオフ、最大数回）。無限リトライ禁止 | NFR-U3-REL-01 |
| **fail-closed** | 認可・検証は失敗時に必ず拒否。例外時にデータ返却しない | SECURITY-15 |
| **グローバル例外ハンドラ** | Lambda ハンドラ最上位で未捕捉例外を捕捉→汎用エラー(5xx)＋構造化ログ。内部詳細を露出しない | SECURITY-15, SECURITY-09 |
| **軽量冪等性** | 問い合わせ二重送信は「同一 email＋message の短時間（例: 数分）重複を無視」。フロントの送信ボタン無効化と併用（Q-D2=A） | NFR-U3-REL, BR-CONTACT |
| **リソース解放** | 例外パスでも接続/一時リソースを確実に解放（with/try-finally） | SECURITY-15 |

## 4. セキュリティパターン（Security）※ Security Baseline

| パターン | 適用 | SECURITY-ID |
|---|---|---|
| **認可の集約（common）** | 認証トークン検証・ロール/オーナー確認を common モジュールに集約。各ハンドラはガード適用 | SECURITY-08/11 |
| **スキーマ検証（境界で検証）** | 全API入力を Pydantic v2 でスキーマ検証（型・長さ・形式・サニタイズ）。パラメータ化アクセスでインジェクション防止 | SECURITY-05 |
| **最小権限IAM** | Lambda 実行ロールは対象テーブル/操作のみ。読み取りと書き込みを別ステートメントに分離。ワイルドカード禁止 | SECURITY-06 |
| **多層防御** | 検証＋認可＋暗号化＋レート制限を重ねる。単一防御に依存しない | SECURITY-11 |
| **レート制限／スロットリング** | 公開API（特に問い合わせ）は API Gateway スロットリング＋バーンスト制限で乱用防止 | SECURITY-11 |
| **秘密情報の外部化** | SES/その他の資格情報は Secrets Manager（または SSM SecureString）。平文/ハードコード禁止 | SECURITY-12 |
| **構造化ログ・PIIマスキング** | 相関ID付きJSONログ。email/message等PIIはログ出力しない（マスク/除外） | SECURITY-03 |
| **監査ログ** | 投稿の公開/非公開、問い合わせ状態遷移は actor/timestamp/before-after を監査記録 | SECURITY-13 |
| **転送/保存時暗号化** | 全通信TLS1.2+、DynamoDB保存時暗号化（AWS管理キー） | SECURITY-01 |

## 5. データ保護・バックアップパターン

| パターン | 適用 | 対応NFR |
|---|---|---|
| **PITR** | DynamoDB Point-in-Time Recovery 有効化（最大35日）。追加スナップショット自動化なし | NFR-U3-BAK-01 |
| **PII最小化** | 問い合わせは name/email/message のみ（Q-F3）。不要なPIIを保持しない | NFR-U3-BAK-03 |

## 6. 観測性パターン（Observability）※後段Infraで具体化

| パターン | 適用 | SECURITY-ID |
|---|---|---|
| **集中ログ** | CloudWatch Logs、ログ保持90日以上、アプリは自ログ削除不可 | SECURITY-03/14 |
| **セキュリティアラート** | 認証失敗・認可違反のアラート（具体閾値は Infrastructure Design） | SECURITY-14 |

## 7. トレーサビリティ

- 反映回答: Q-D1=A / Q-D2=A / Q-D3=A（`../../plans/u3-backend-api-nfr-design-plan.md`）
- 参照NFR: NFR-U3-PERF/SCALE/AVAIL/REL/BAK-*, SECURITY-01/03/05/06/08/11/12/13/14/15
- 参照機能設計: `../functional-design/business-rules.md`（BR-CONTACT/BR-SEC/BR-STATE）
