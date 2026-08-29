# Infrastructure Design — U3 backend-api（IYフレンズ）

論理コンポーネント（`../nfr-design/logical-components.md`）を AWS 物理リソースへ対応付ける。
確定回答: Q-I1=A（AWS SAM）/ Q-I2=A（マルチテーブル）/ Q-I3=A（SSM Parameter Store SecureString）/ Q-I4=A（本番のみ開始）。
リージョン: **ap-northeast-1（東京）単一**。方針: 最安・サーバーレス・最小権限。

---

## 1. 論理 → 物理 対応表

| 論理コンポーネント | AWS リソース | 主要設定 |
|---|---|---|
| API公開 | **API Gateway（HTTP API）** | 単一API、ステージ `prod`、スロットリング（レート/バースト上限）、Cognito JWTオーソライザ（管理系）、CORSはオリジン限定 |
| content/calendar/contact 実行 | **AWS Lambda（Python 3.13）** | モジュール別関数（またはモノリシック1関数＋内部ルーティング。SAMで定義）。メモリ最小（128–256MB目安）、タイムアウト適切、環境変数は非機密のみ |
| 認証 | **Amazon Cognito User Pool** | 管理者/編集者。MFA（管理者必須）、パスワードポリシー（8文字以上・漏洩チェック）、ブルートフォース対策 |
| データ | **DynamoDB（マルチテーブル, On-Demand）** | テーブル: `Posts` `Notices` `Events` `Inquiries` `Users`。PITR有効、保存時暗号化（AWS管理キー）、必要なGSI |
| 通知メール | **Amazon SES** | 送信元ドメイン/アドレス検証、同期送信、送信失敗はログ＋Inquiry通知ステータス記録 |
| 秘密情報/設定 | **SSM Parameter Store（SecureString）** | SES設定・通知先等。KMS(AWS管理キー)で暗号化。平文/ハードコード禁止 |
| ログ/監視 | **CloudWatch Logs / Alarms** | ロググループ保持90日、相関ID付き構造化ログ、認証失敗・認可違反アラート |
| 権限 | **IAM ロール（Lambda実行ロール）** | 最小権限。対象テーブル/操作/パラメータのみ。読み書き分離、ワイルドカード禁止 |

## 2. DynamoDB テーブル設計（マルチテーブル, Q-I2=A）

| テーブル | PK | SK | 主なGSI | 備考 |
|---|---|---|---|---|
| `Posts` | `postId` | — | `GSI-published`（status=published, publishedAt降順） | ブログ記事。カテゴリ属性 |
| `Notices` | `noticeId` | — | `GSI-published`（status, publishedAt降順） | お知らせ |
| `Events` | `eventId` | — | `GSI-date`（eventDate昇順） | カレンダー用イベント |
| `Inquiries` | `inquiryId` | — | `GSI-status`（status, createdAt降順） | 問い合わせ。PII（name/email/message）。status=未対応/対応中/対応済 |
| `Users` | `userId` | — | — | Cognito sub と対応。ロール等の付随情報（最小限） |

- 一覧は GSI で公開・日付順に Query、10件/ページ（LastEvaluatedKeyカーソル）。Scanは使わない。
- 全テーブル: On-Demand、PITR ON、SSE(保存時暗号化) ON。

## 3. IAM 最小権限（SECURITY-06）方針

- Lambda 実行ロールは、そのモジュールが触るテーブル/インデックス/操作のみ許可
  - content 関数: `Posts`/`Notices` の必要操作（読みと書きを別ステートメント）
  - calendar 関数: `Events`
  - contact 関数: `Inquiries`（Put/Query/Update）＋ SES `SendEmail`＋ SSM `GetParameter`（該当パラメータのみ）
- リソースは具体的 ARN 指定、ワイルドカード禁止。ログ書き込みは対象ロググループに限定。
- CloudWatch ロググループの削除権限は付与しない（SECURITY-14 自ログ改変防止）。

## 4. ネットワーク / 公開（SECURITY-07/02/04）

- サーバーレスのためVPCは原則不要（DynamoDB/SES/Cognito はパブリックエンドポイント＋IAM/TLSで保護）。VPC/NATは導入しない（コスト）。
- 公開は 80/443 のみ（CloudFront/API Gateway 経由）。0.0.0.0/0 の無制限開放なし。
- **アクセスログ有効化**（SECURITY-02）: API Gateway 実行/アクセスログ → CloudWatch。CloudFront標準ログ（U5で最終化）。
- **HTTPセキュリティヘッダ**（SECURITY-04）: HTML配信は U1/U5（CloudFront）側で CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy を付与 → U5 申し送り。API(JSON)応答にも最小限のセキュリティヘッダを付与。

## 5. ハードニング / 供給網（SECURITY-09/10）

- **SECURITY-09**: デフォルト認証情報なし、本番エラーは汎用メッセージ（スタックトレース非表示）、S3はU5でパブリックアクセスブロック、サンプル/デモ非デプロイ、ランタイムは現行サポート版。
- **SECURITY-10**: 依存はロックファイルで固定、CIで脆弱性スキャン、`latest`タグ不使用、公式レジストリのみ、本番はSBOM生成（詳細は Build and Test / Code Generation）。

## 6. コスト見積り（目安）

| リソース | 想定 | 月額目安 |
|---|---|---|
| Lambda | 小規模呼び出し・無料枠内が大半 | ほぼ0円 |
| API Gateway(HTTP API) | 低リクエスト | 数十円 |
| DynamoDB On-Demand + PITR | 小容量 | 数十円〜 |
| Cognito | MAU少数（無料枠内が多い） | ほぼ0円 |
| SES | 低送信量 | ほぼ0円 |
| SSM Parameter Store(SecureString) | 標準パラメータ | 実質0円 |
| CloudWatch Logs | 低ログ量・90日保持 | 数十円 |

→ 合計 **月 数百円規模**（NFR-COST-01 と整合）。

## 7. トレーサビリティ

- 反映回答: Q-I1..I4 = A（`../../plans/u3-backend-api-infrastructure-design-plan.md`）
- 参照: `../nfr-design/logical-components.md`, `../nfr-requirements/tech-stack-decisions.md`
- 対応SECURITY: 01/02/03/04/06/07/09/10/12/14（U3インフラ観点）
- 申し送り: 共有インフラは `shared-infrastructure.md` 参照（U5で集約）
