# Code Generation 計画 — U5 infra（IYフレンズ / Phase 1）

U5 の共有インフラを **AWS SAM**（Q-U1=A）で IaC 化する。**この計画がCode Generationの唯一の正**とする。

---

## 1. ユニットコンテキスト
- **配置（ワークスペース直下）**: `C:\Users\syuto\IY FRIENDS\iyf-infra\`
- **ドキュメント**: `aidlc-docs/construction/u5-infra/code/`（Markdown要約のみ）
- **スタック**: `iyf-infra-shared`（S3/CloudFront/Cognito/監視）。U3 backend スタックとはクロススタック参照
- **担当範囲**: 共有インフラのみ（backend の Lambda/API/DynamoDB は U3 所有）
- **ストーリー**: US-18（セキュリティ横断・主）、US-19（低コスト・主）、US-13(SES基盤)/US-15/16(Cognito基盤) の土台提供

## 2. 生成ステップ（番号順・チェックボックス）

### Step 1: プロジェクト構成（Greenfield）
- [x] `iyf-infra/` 骨組み、`samconfig.toml`（prod, ap-northeast-1）、`README.md`、`.gitignore`

### Step 2: 共有インフラ SAM テンプレート
- [x] `iyf-infra/template.yaml`：
  - S3 バケット（Web資材）：パブリックアクセスブロック、暗号化、OACのみ許可（SECURITY-09/01）
  - CloudFront：S3 オリジン(OAC)、Response Headers Policy（CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy, SECURITY-04）、標準ログ、TLS1.2+
  - Cognito User Pool + Client：MFA（管理者必須相当設定）、パスワードポリシー（8文字以上）、グループ admin/editor（SECURITY-12）
  - CloudWatch Alarms（最小）：API 5xx、Lambda エラー、（Cognito）サインイン失敗系。ログ保持90日（SECURITY-14）
  - Outputs（Export）：CloudFrontDomain, WebBucketName, UserPoolId, UserPoolClientId

### Step 3: パラメータ / 環境
- [x] `template.yaml` パラメータ：Stage、（将来）独自ドメイン/証明書ARN（任意）
- [x] デフォルトは Phase 1（デフォルトドメイン、独自ドメインなし）

### Step 4: 検証（テンプレート妥当性）
- [x] `sam validate` 相当の構文/参照チェック（ローカルで YAML 構文確認）

### Step 5: ドキュメント / 要約
- [x] `iyf-infra/README.md`（デプロイ手順・Outputs・連携）
- [x] `aidlc-docs/construction/u5-infra/code/code-generation-summary.md`（生成物・Export一覧・セキュリティ適合）

## 3. セキュリティ適合（IaC層）
SECURITY-01（暗号化/TLS）, 02（アクセスログ）, 04（セキュリティヘッダ）, 06（OAC最小権限）, 09（S3公開ブロック）, 12（Cognito MFA/ポリシー）, 14（アラート・ログ90日）。

## 4. トレーサビリティ
- 設計参照: `../u5-infra/infrastructure-design/*`, `../shared-infrastructure.md`
- 総ステップ数: 5
