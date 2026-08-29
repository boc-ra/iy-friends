# iyf-infra（IYフレンズ 共有インフラ / U5）

IY Friends サイトの**共有インフラ**を AWS SAM で定義する。
バックエンド（Lambda/API/DynamoDB）は U3 `iyf-backend-api` が所有。本スタックはそれ以外の共有部分を担当。

## 含むもの（Phase 1+2）
- **S3**（Web資材ホスティング, パブリックブロック, 暗号化, OACのみ許可）
- **CloudFront**（S3配信, セキュリティヘッダ[CSP/HSTS等], TLS1.2+, ディープリンク対応）
- **Cognito**（管理者/編集者。TOTP MFA, パスワードポリシー, admin/editorグループ, 招待制, Advanced Security）
  - **Phase 2**: トークン有効期限を明示（access/id=1h, refresh=30d）。admin の MFA 必須は admin-web ログインフローで強制（`MfaConfiguration=OPTIONAL` 維持で editor 任意）
- **監視**（最小: API 5xx / Lambda エラーの CloudWatch アラーム → SNS、ログ保持90日）

## デプロイ
```bash
sam validate
sam deploy --guided     # 初回。以降 sam deploy
# 主なパラメータ:
#   Stage=prod
#   ApiName=<U3のAPI名>            （監視する場合。空でスキップ可）
#   BackendFunctionName=<U3関数名>  （監視する場合）
#   AlarmEmail=<通知先メール>       （SNS購読。空でスキップ）
```

## Outputs（他ユニットが参照）
| Export 名 | 用途 |
|---|---|
| `iyf-<stage>-CloudFrontDomain` | 公開URL（U1/告知） |
| `iyf-<stage>-WebBucketName` | フロント資材アップロード先（U1 デプロイ） |
| `iyf-<stage>-UserPoolId` | API オーソライザ（U3, Phase 2） |
| `iyf-<stage>-UserPoolClientId` | 管理フロント認証（U2） |

## デプロイ順序（Phase 1）
U3 backend → **U5 shared（本スタック）** → U1 frontend（S3同期→CloudFront無効化）→ U3 CORS更新

## Phase 2（管理CMS 認証）
デプロイ順序: **U5 shared（本スタック更新）** → U3 backend（AdminFunction/JWTオーソライザ、U5 Export を Import）→ backfill → U2 admin-web。

### 初期 admin ブートストラップ（1回・手動）
最初の管理者は招待元が居ないため手動投入する:
```bash
POOL=$(aws cloudformation list-exports \
  --query "Exports[?Name=='iyf-prod-UserPoolId'].Value" --output text)

aws cognito-idp admin-create-user --user-pool-id "$POOL" \
  --username "admin@example.com" \
  --user-attributes Name=email,Value="admin@example.com" Name=email_verified,Value=true \
  --desired-delivery-mediums EMAIL

aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" \
  --username "admin@example.com" --group-name admin
```
本人が初回ログイン（仮PW→新PW）→ admin-web で TOTP 登録（admin は必須）→ displayName 設定。
以後の編集者は admin が admin-web の招待機能（U3 `POST /admin/users/invite`）で追加。

## 独自ドメイン（将来 / NFR-DOM-02）
Phase 1 は CloudFront デフォルトドメイン（0円）。独自ドメイン追加時は us-east-1 の ACM 証明書と
`ViewerCertificate` / `Aliases` を追加する（テンプレートにパラメータ拡張ポイントあり）。

## セキュリティ（IaC層）
SECURITY-01（暗号化/TLS）/02（ログ）/04（ヘッダ）/06（OAC最小権限）/09（S3公開ブロック）/12（Cognito）/14（アラート・90日保持）。
# GitHub Actions OIDC bootstrap

`github-actions-bootstrap.yaml` creates the GitHub OIDC Provider, an encrypted SAM artifact bucket, a GitHub deployment role, and a separate CloudFormation execution role. It does not deploy either application stack.

Because repositories created after 2026-07-15 use immutable GitHub OIDC subjects, both the account/organization numeric ID and repository numeric ID are required in addition to their names.

Validate before deployment:

```powershell
sam validate --lint --template-file github-actions-bootstrap.yaml
```

Create the stack only from an authenticated AWS SSO administrator session and only after explicit production authorization:

```powershell
sam deploy `
  --template-file github-actions-bootstrap.yaml `
  --stack-name iyf-github-actions-prod `
  --capabilities CAPABILITY_NAMED_IAM `
  --parameter-overrides `
    GitHubOwner=<owner> `
    GitHubOwnerId=<numeric-owner-id> `
    GitHubRepository=iy-friends `
    GitHubRepositoryId=<numeric-repository-id> `
    GitHubEnvironment=production `
  --region ap-northeast-1 `
  --confirm-changeset
```

Copy the stack outputs into GitHub `production` Environment variables:

| Stack output | GitHub variable |
|---|---|
| `AwsAccountId` | `AWS_ACCOUNT_ID` |
| `GitHubDeploymentRoleArn` | `AWS_DEPLOY_ROLE_ARN` |
| `CloudFormationExecutionRoleArn` | `AWS_CFN_EXECUTION_ROLE_ARN` |
| `DeploymentArtifactBucketName` | `AWS_SAM_ARTIFACT_BUCKET` |

Restrict the Environment to the `main` branch and configure an approval reviewer. Run the production workflow with `deploy=false` first to verify OIDC without changing application resources.
