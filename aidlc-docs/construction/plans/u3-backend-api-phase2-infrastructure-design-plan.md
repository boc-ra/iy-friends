# U3 backend-api (Phase 2) — Infrastructure Design Plan

**対象**: U3 Phase 2（管理API）の論理→物理マッピング（SAM 追加分）。
**前提**: Phase 1 backend `template.yaml`（単一 HttpApi + 単一 PublicFunction + 5テーブル）、U5 `iyf-infra`（Cognito UserPool/Client/admin&editorグループを構築済・`iyf-${Stage}-UserPoolId`/`-UserPoolClientId` を Export）。

## 現行把握（重要）
- backend は **単一 HttpApi**・**単一 Lambda（PublicFunction, 内部ルーティング）**。
- `GSI-published` は **sparse index**（`gsi_status` を published 時のみ設定）→ draft 含む管理系一覧には**常時設定の `status` 属性 + 新 GSI** が必要。
- Inquiries は実装上 **`GSI-dedup` のみ**（status GSI 未実装）→ 管理系 listInquiries(status) 用に **`GSI-status` 追加**。
- Cognito は U5 に存在（TOTP・招待制 AllowAdminCreateUserOnly・AdvancedSecurity ENFORCED）。U3 は Import 参照。

## 設計判断（ユーザー質問なしで確定 — 既存構造から一意。**変更可**）
- [x] **API 構成**: 既存 **単一 HttpApi を維持**し、**管理ルートにのみ JWT オーソライザ**を付与（HTTP API のルート単位オーソライザ）。別 AdminApi は作らない（低コスト・簡潔）。
- [x] **Lambda 構成**: 既存 PublicFunction と並べて **単一 `AdminFunction`（`src.handlers.admin.handler`, 内部ルーティング）**を追加（モジュラモノリス踏襲）。
- [x] **JWT オーソライザ**: issuer=`https://cognito-idp.${Region}.amazonaws.com/<UserPoolId>`、audience=`<UserPoolClientId>`。両値は **`Fn::ImportValue`** で U5 スタック Export から取得（同一 region/account）。
- [x] **DynamoDB 追加**: Posts/Notices に **`GSI-status`（HASH=`status`(常時), RANGE=`updated_at_epoch`）** 追加。Inquiries に **`GSI-status`（HASH=`status`, RANGE=`created_at_epoch`）** 追加。Users は GSI 追加なし（listUsers=Scan≤10）。
- [x] **IAM（最小権限, SECURITY-06）**: AdminFunction 実行ロールに DynamoDB CRUD（Posts/Notices/Events/Inquiries/Users）＋新GSI Query、**cognito-idp Admin 操作**（AdminCreateUser/AdminAddUserToGroup/AdminDisableUser/AdminEnableUser/ListUsers/AdminGetUser）を **Import した UserPool ARN 限定**、SSM 参照、対象ロググループのみ。ワイルドカード禁止。
- [x] **CORS**: admin ルート用に PUT/DELETE メソッドと `Authorization` ヘッダを許可（オリジンは admin-web 限定）。
- [x] **監査/ログ**: AdminFunction 専用ロググループ（90日保持）。監査は CloudWatch 構造化ログ（専用テーブルなし）。
- [x] **U5 への申し送り**（Phase 2 調整）: (a) Admin グループへ MFA 強制（PreTokenGeneration/PreAuth トリガ or admin-web フロー強制。現状 MfaConfiguration=OPTIONAL）、(b) UserPoolClient に明示 Token 有効期限（access/id=1h, refresh=30d）と `ALLOW_USER_SRP_AUTH` 確認、(c) 初期 admin ブートストラップ手順。
- [x] infrastructure-design-phase2.md / deployment-architecture-phase2.md 生成、shared-infrastructure.md に Phase 2 追記

> 変更したい場合は「Request Changes」で（特に: 単一API+ルート認可 vs 別AdminApi、単一AdminFunction vs モジュール別関数、GSI 命名/射影）。
