# Deployment Architecture（Phase 2 追補）— U5 infra

Phase 1 `deployment-architecture.md` を継承。Phase 2（認証仕上げ）のデプロイ順序・手順。

## 1. デプロイ順序（Phase 2 全体, 再掲）
```
1. U5 infra（iyf-infra）更新   ← 本ユニット（Cognito token 有効期限明示。Export 維持）
2. U3 backend-api 更新          ← AdminFunction / GSI-status / JWT オーソライザ（U5 Export を Import）
   └ その後 backfill_status 実行
3. 初期 admin ブートストラップ（下記 §2）
4. U2 admin-web デプロイ         ← MFA 強制フロー実装、U5 の UserPoolId/ClientId を使用
```
- U5 更新は既存 Export を維持するため U3 の Import を壊さない（後方互換）。

## 2. 初期 admin ブートストラップ手順（runbook, 1回・手動）
```bash
POOL=$(aws cloudformation list-exports \
  --query "Exports[?Name=='iyf-prod-UserPoolId'].Value" --output text)

# 1) 管理者ユーザー作成（招待メール＋仮パスワード送付）
aws cognito-idp admin-create-user \
  --user-pool-id "$POOL" \
  --username "admin@example.com" \
  --user-attributes Name=email,Value="admin@example.com" Name=email_verified,Value=true \
  --desired-delivery-mediums EMAIL

# 2) admin グループへ追加
aws cognito-idp admin-add-user-to-group \
  --user-pool-id "$POOL" --username "admin@example.com" --group-name admin

# 3) 本人が初回ログイン（仮PW→新PW）→ admin-web で TOTP 登録（MFA 必須）→ displayName 設定
```
> 以後の編集者は admin が admin-web の「招待」機能（U3 `POST /admin/users/invite`）で追加。

## 3. ロールバック / リスク
- 変更は Cognito Client のトークン有効期限のみ（UserPool 本体・Export は不変）。影響は限定的。
- 既存ログイン中セッションは新しい RefreshTokenValidity が次回更新時に反映。

## 4. トレーサビリティ
- 参照: `infrastructure-design-phase2.md`, `../../shared-infrastructure.md` §3b
- 依存: Phase 2 順序（U5→U3→U2）= `inception/application-design/unit-of-work-dependency.md`
