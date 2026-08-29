# Infrastructure Design — U5 infra（IYフレンズ）

U5 は共有インフラ（フロント配信・認証・ドメイン・監視）を確定・IaC化するユニット。
確定回答: Q-U1=A（SAM統一・U5は共有インフラのみ）/ Q-U2=A（デフォルトドメイン）/ Q-U3=A（標準セキュリティヘッダ）/ Q-U4=A（最小監視）/ Q-U5=A（Phase 1でCognito）。
リージョン: ap-northeast-1（東京）※CloudFront/ACM の一部はグローバル/us-east-1 に留意。

> IaC 方針変更の記録: Inception の unit-of-work.md では U5=CDK だったが、U3 が SAM で構築済みのため、**ツール統一の観点で U5 も SAM に変更**（Q-U1=A）。U5 は「共有インフラのみ」を別 SAM スタックで定義し、U3 バックエンドスタックとはクロススタック参照で連携する。

---

## 1. U5 の担当範囲（共有インフラ）

| 論理 | AWS リソース | 主要設定 | 対応 |
|---|---|---|---|
| 静的配信 | **CloudFront** | OAC 経由で S3 参照、キャッシュ、**Response Headers Policy（CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy）**、標準アクセスログ | SECURITY-04/02, NFR-PERF-02 |
| 静的ホスティング | **S3（Web資材/画像）** | **パブリックアクセスブロック**、OAC のみ許可、保存時暗号化 | SECURITY-09/01 |
| 認証 | **Cognito User Pool ＋ Client** | 管理者/編集者、**MFA（管理者必須）**、パスワードポリシー（8文字以上・漏洩チェック）、ブルートフォース対策 | SECURITY-12 |
| ドメイン | **CloudFront デフォルトドメイン**（Phase 1） | `*.cloudfront.net`（0円）。将来 Route53+ACM で独自ドメイン追加可 | NFR-DOM-01/02 |
| 監視 | **CloudWatch Alarms（最小）** | Lambda エラー率 / API 5xx / 認証失敗 のアラート。ログ保持90日、アプリは自ログ削除不可 | SECURITY-14, NFR-OPS-03 |
| 連携 | **クロススタック参照** | U3 バックエンド SAM スタックの API エンドポイント/Cognito を Export/Import または SSM Parameter で共有 | — |

## 2. U3（backend）と U5（shared）の責務分界

| 項目 | 所有 |
|---|---|
| Lambda / API Gateway(HTTP API) / DynamoDB×5 / backend IAM | **U3**（`iyf-backend-api/template.yaml`） |
| S3 / CloudFront / Cognito / ドメイン / 集中監視 | **U5**（`iyf-infra/`） |
| API への認可（Cognito オーソライザ） | U5 が User Pool 提供 → U3 が Import して API に適用 |
| フロント → API 呼び出し | U1 が CloudFront 配下、API は U3。CORS 許可オリジン（CloudFront ドメイン）を U3 に設定 |

## 3. セキュリティ担保（U5 が最終担保する項目）

| SECURITY-ID | U5 での担保 |
|---|---|
| SECURITY-01 | S3/転送の暗号化、TLS1.2+（CloudFront 最小プロトコル） |
| SECURITY-02 | CloudFront 標準ログ、API Gateway アクセスログ（U3側設定）を集約 |
| SECURITY-04 | CloudFront Response Headers Policy で HTML にセキュリティヘッダ付与 |
| SECURITY-06 | CloudFront→S3 は OAC のみ（最小権限）。IAM ワイルドカード禁止 |
| SECURITY-09 | S3 パブリックアクセスブロック、デフォルト認証情報なし |
| SECURITY-12 | Cognito：MFA・パスワードポリシー・ブルートフォース対策 |
| SECURITY-13 | CloudFront 経由の外部スクリプトは SRI（フロント=U1と連携） |
| SECURITY-14 | 認証失敗/認可違反アラート、ログ保持90日、ログ改変防止 |

## 4. コスト（U5 追加分の目安）
CloudFront（低トラフィック・無料枠中心）／S3（小容量）／Cognito（MAU少数・無料枠）／CloudWatch（最小アラーム）
→ いずれも **ほぼ0〜数十円/月**。U3 と合算しても月 数百円規模（NFR-COST-01 維持）。

## 5. 後段への申し送り
- **Code Generation（U5）**: `iyf-infra/` に SAM テンプレート実体（shared スタック）を生成
- **U1 public-web**: CloudFront ディストリビューション名/S3バケット/API ベースURL/Cognito Client ID を参照
- **U3 更新**: Cognito User Pool ARN を Import し API オーソライザに適用（Phase 2 で有効化）、CORS 許可オリジンに CloudFront ドメインを設定

## 6. トレーサビリティ
- 反映回答: Q-U1..U5 = A（`../../plans/u5-infra-infrastructure-design-plan.md`）
- 参照: `../../shared-infrastructure.md`, `../../u3-backend-api/infrastructure-design/*`
- 対応: SECURITY-01/02/04/06/09/12/13/14, NFR-DOM-01/02, NFR-OPS-03, NFR-PERF-02, NFR-COST-01
