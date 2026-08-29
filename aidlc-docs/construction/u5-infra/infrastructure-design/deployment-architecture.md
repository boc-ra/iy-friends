# Deployment Architecture — U5 infra（IYフレンズ）

IaC: **AWS SAM**（Q-U1=A、U3 と統一）。リポジトリ: `iyf-infra/`。環境: `prod`（U3 と同方針）。

---

## 1. スタック構成（マルチスタック）

```
[ iyf-backend-api (U3, 既存) ]   ← Lambda / API Gateway / DynamoDB×5 / backend IAM
        ▲ Import (API URL)             ▲ Import (Cognito ARN)  ※Phase 2で有効化
        │                              │
[ iyf-infra-shared (U5, 新規) ]
   - S3 (web資材, パブリックブロック, OAC)
   - CloudFront (S3 origin, Response Headers Policy, ログ)
   - Cognito User Pool + Client (MFA/パスワードポリシー)
   - CloudWatch Alarms (Lambdaエラー/API5xx/認証失敗) + ログ保持90日
   - (将来) Route53 + ACM (独自ドメイン)
```

- **連携方式**: CloudFormation Export/Import または SSM Parameter。
  - U5 → 出力: CloudFront ドメイン、S3 バケット名、Cognito UserPoolId / ClientId
  - U3 → 参照: Cognito ARN（API オーソライザ, Phase 2）、CORS 許可オリジン（CloudFront ドメイン）

## 2. デプロイ順序（Phase 1）
1. **U3 backend**（`iyf-backend-api`）: `sam deploy`（API/DynamoDB） … 済/可
2. **U5 shared**（`iyf-infra`）: `sam deploy`（S3/CloudFront/Cognito/監視）
3. **U1 frontend**（`iyf-public-web`）: ビルド成果物を S3 へ同期 → CloudFront 無効化
4. **U3 再更新**（任意）: CORS 許可オリジンに CloudFront ドメインを設定

> 注: U5 は U3 の API を参照するが、Phase 1 の公開読み取りは未認証のため、Cognito 連携（オーソライザ適用）は Phase 2 で有効化。

## 3. リージョン留意点
- CloudFront はグローバル、**ACM 証明書（独自ドメイン時）は us-east-1** が必要。
- それ以外（S3/Cognito/監視）は ap-northeast-1。

## 4. ロールバック / 変更管理
- 各 SAM スタックは変更セット＋自動ロールバック。
- CloudFront 設定変更はディストリビューション更新（反映に数分）。

## 5. 後段への申し送り（Code Generation）
- `iyf-infra/template.yaml`（shared スタック実体）を生成
- S3 バケットポリシー（OAC のみ）、CloudFront Response Headers Policy（CSP/HSTS等）
- Cognito UserPool（MFA/パスワードポリシー/グループ: admin/editor）
- CloudWatch Alarms 定義、Outputs（Export 名）
