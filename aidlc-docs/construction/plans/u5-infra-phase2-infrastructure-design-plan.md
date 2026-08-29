# U5 infra (Phase 2) — Infrastructure Design Plan & Question

**対象**: U5 infra（Phase 2 認証仕上げ）。Phase 1 で Cognito UserPool/Client/admin&editorグループ・Export は構築済み。
**前提（確定・再質問しない）**: 東京単一リージョン / 低コスト / SAM / Cognito TOTP・招待制(AllowAdminCreateUserOnly)・AdvancedSecurity ENFORCED は既存維持。U3 は `iyf-${Stage}-UserPoolId`/`-UserPoolClientId` を Import 参照（**Export は削除・改名しない**）。
**インフラユニットのため Functional/NFR/NFR-Design はスキップ**（Phase 1 U5 と同方針。要件は Infra へ集約）。

## Phase 2 で加える変更（3点）
1. **Admin MFA 強制**（現状 OPTIONAL）← 下記 Question で方式決定
2. **トークン有効期限の明示**: UserPoolClient に `AccessTokenValidity=1h` / `IdTokenValidity=1h` / `RefreshTokenValidity=30d`（N3=A）。未指定時の既定と一致するが明示化
3. **初期 admin ブートストラップ手順**（運用 runbook）: 最初の管理者を投入（AdminCreateUser + admin グループ + 初回 MFA 設定）

## 設計プラン（チェックボックス）
- [x] MFA 強制方式の確定 → **A**（admin-web フロー強制・MfaConfiguration=OPTIONAL 維持）
- [x] UserPoolClient にトークン有効期限を明示（1h/1h/30d）
- [x] admin-web は SRP 直叩き（Amplify/SDK）想定 → Hosted UI コールバック不要（CallbackURLs 不要）。CORS は U3 API 側で対応
- [x] 初期 admin ブートストラップ手順を runbook 化
- [x] infrastructure-design-phase2.md / deployment-architecture-phase2.md 生成、shared-infrastructure.md 追記

---

## Question U5-1 — Admin の MFA 強制方式（N1=A: Admin 必須 / Editor 任意）
Cognito の `MfaConfiguration` は「全員必須(ON)」か「任意(OPTIONAL)」しか選べず、「admin グループのみ必須」をネイティブ指定できません。どう強制しますか？

A) **admin-web のログインフローで強制**（MfaConfiguration=OPTIONAL 維持）。admin グループのユーザーは初回ログイン時に TOTP 登録を必須化し、未設定なら管理画面に入れない。追加インフラなし・低コスト（推奨）。enforcement は主にアプリ層 + Cognito Advanced Security の異常検知で補完

B) **PreAuthentication/PreTokenGeneration Lambda トリガで強制**（サーバー側で admin×MFA未設定を拒否）。堅牢だが U5 に Lambda を追加（コード・監視・コスト増）

C) **MfaConfiguration=ON（全員必須）**。editor も MFA 必須になる（N1=A の「editor 任意」と矛盾するが、全員に強制したい場合）

X) Other（[Answer]: の後に記述）

[Answer]: A （推奨既定を適用：ユーザー「Done」時に空欄のため。変更可）

---

**回答後「done」等でお知らせください。** 空欄なら推奨(A)を適用して進めます。回答を反映して infrastructure-design 成果物を生成します。
