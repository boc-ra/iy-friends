# Code Generation Summary — U5 infra（Phase 1）

生成場所: ワークスペース直下 `iyf-infra/`（共有インフラ SAM スタック）。

## 生成ファイル
| ファイル | 内容 |
|---|---|
| `iyf-infra/template.yaml` | 共有インフラ SAM（14リソース） |
| `iyf-infra/samconfig.toml` | prod / ap-northeast-1 |
| `iyf-infra/README.md` | デプロイ手順・Outputs・連携 |
| `iyf-infra/.gitignore` | — |
| `aidlc-docs/construction/u5-infra/code/code-generation-summary.md` | 本書 |

## リソース内訳（14）
- **S3**: WebBucket（公開ブロック/暗号化/バージョニング）＋ WebBucketPolicy（OACのみ許可）
- **CloudFront**: OAC / SecurityHeadersPolicy（CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy）/ Distribution（S3配信・TLS・ディープリンク対応）
- **Cognito**: UserPool（MFA/パスワードポリシー/招待制/Advanced Security）/ UserPoolClient / AdminGroup / EditorGroup
- **監視**: AlarmTopic(SNS) / AlarmSubscription(条件) / Api5xxAlarm(条件) / LambdaErrorAlarm(条件) / SharedLogGroup(保持90日)

## Outputs（Export：他ユニット参照）
`CloudFrontDomain` / `WebBucketName` / `UserPoolId` / `UserPoolClientId`

## 検証
- ローカルで YAML 構文＋構造チェック **PASS**（`sam validate` は AWS 環境で実施）。
- 条件（Condition）で ApiName/BackendFunctionName/AlarmEmail 未指定時はアラーム/購読をスキップ可能。

## セキュリティ適合（IaC層）
SECURITY-01（暗号化/TLS）/02（ログ）/04（ヘッダ）/06（OAC最小権限）/09（S3公開ブロック）/12（Cognito MFA・ポリシー・Advanced Security）/14（アラート・ログ90日）。

## ストーリー対応
US-18（セキュリティ横断・主）／US-19（低コスト・主）／US-13（SES土台はU3、通知先はSSM）／US-15/16（Cognito基盤を提供、認証本実装はPhase 2 U3 auth）。

## 後段への申し送り
- **U1 public-web**: `WebBucketName` へ資材同期、`CloudFrontDomain` を公開URLに、`UserPoolClientId` は管理フロント(U2)。
- **U3**: `UserPoolId` を API オーソライザに適用（Phase 2）、CORS 許可オリジンに CloudFront ドメイン設定。
