# Code Generation Summary（Phase 2）— U5 infra

ブラウンフィールド（既存 `iyf-infra/` を修正）。IaC のみの最小変更。

## 修正（Modified）
- `iyf-infra/template.yaml`
  - `UserPoolClient` に **トークン有効期限を明示**: `TokenValidityUnits`（AccessToken/IdToken=hours, RefreshToken=days）＋ `AccessTokenValidity: 1` / `IdTokenValidity: 1` / `RefreshTokenValidity: 30`（N3=A）
  - `MfaConfiguration` コメントを Phase2/U5-1=A（admin-web フロー強制）に更新。値は `OPTIONAL` 維持（editor 任意）
  - Description を Phase 1+2 に更新
- `iyf-infra/README.md` — Phase 2（トークン寿命・admin MFA 方式）＋ 初期 admin ブートストラップ runbook を追記

## 意図的に変更しなかったもの（後方互換の要）
- **Export（`iyf-<stage>-UserPoolId` / `-UserPoolClientId`）** — U3 が `Fn::ImportValue` で参照するため名称不変
- UserPool 本体（TOTP・招待制・PasswordPolicy・AdvancedSecurity・admin/editorグループ）
- Lambda は追加しない（U5-1=A の利点。MFA 強制は admin-web 側）

## デプロイ・検証
- `sam validate` / `sam deploy` は Build & Test（Phase 2）で実施（本環境に SAM CLI 無し）。
- 変更は Cognito Client 設定のみで低リスク。既存 Export・UserPool ID は不変のため U3 の Import を壊さない。

## トレーサビリティ
- 反映: U5-1=A, N3=A
- 参照: `../infrastructure-design/infrastructure-design-phase2.md`, `../../shared-infrastructure.md` §3b
- 申し送り（U2 admin-web）: admin グループの初回 TOTP 登録強制フローを実装（`infrastructure-design-phase2.md` §3）
