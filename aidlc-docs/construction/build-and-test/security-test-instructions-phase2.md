# Security Test Instructions（Phase 2）

Security Baseline（有効）に基づく管理系の検証。

## 認証・認可（SECURITY-08/12）
- [ ] 未認証で `/admin/*` → **401**（deny-by-default）。
- [ ] editor が Admin 専用（inquiries/users）→ **403**。
- [ ] editor が他人の記事を update/delete/status → **403**（IDOR 防止, `require_owner`）。
- [ ] 管理者ログインで **MFA(TOTP) が要求**される（未登録なら登録強制）。editor は任意。
- [ ] トークン改ざん/失効 → API Gateway JWT オーソライザで拒否。

## 入力検証・XSS（SECURITY-05）
- [ ] 本文（TipTap）に `<script>` を混入 → バックエンド `bleach` allowlist で除去（保存/表示時）。
- [ ] 過大な title/body/email → 422/400。
- [ ] 招待 email 形式不正 → 422/400。

## 秘密情報・最小権限（SECURITY-06/12）
- [ ] AdminFunction IAM は対象テーブル/GSI + cognito-idp（UserPool ARN 限定）+ SSM プレフィックスのみ（ワイルドカードなし）。
- [ ] Cognito App Client secret 不使用（SPA 公開クライアント）。

## 監査・ロギング（SECURITY-03/13/14）
- [ ] 管理系ミューテーション（create/publish/delete/invite/setStatus）が CloudWatch 構造化ログに記録（actor/action/target）。PII/本文は出力しない。
- [ ] 401/403 がログ・アラート対象。ロググループ保持 90 日。

## 依存・供給網（SECURITY-10）
- [ ] backend: requirements/pyproject でバージョン固定（bleach 追加）。CI で脆弱性スキャン。
- [ ] admin-web: `npm audit`（既知脆弱性の確認）。依存はロック（package-lock.json）。

## 実施メモ
- 自動化可能な項目（401/403/422、サニタイズ）は backend の pytest（`test_handlers_admin`/`test_content_admin`/`test_auth`）で一部カバー済み。
- MFA/トークン/IAM/監査はデプロイ環境で手動確認（or 将来の e2e/権限テスト）。
