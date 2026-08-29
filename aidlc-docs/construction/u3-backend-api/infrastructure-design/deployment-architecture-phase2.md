# Deployment Architecture（Phase 2 追補）— U3 backend-api

Phase 1 `deployment-architecture.md` を継承。Phase 2（管理API）のデプロイ構成・順序・依存を示す。

---

## 1. Phase 2 デプロイ構成図（テキスト）
```
[admin-web (U2, SPA)]
   │  Cognito ログイン(SRP, MFA) → JWT(access/id)
   │  Authorization: Bearer <access>
   ▼
[CloudFront (U5, 管理配信) ]  →  [API Gateway HTTP API (U3, 既存)]
                                     │  管理ルート: JWT オーソライザ（Cognito 検証）
                                     ▼
                              [Lambda AdminFunction (U3, 新規)]
                                     │  common.auth: require_role / require_owner
                                     ├─→ DynamoDB: Posts/Notices(+GSI-status), Events, Inquiries(+GSI-status), Users
                                     └─→ Cognito(U5): AdminCreateUser / Group / Disable / Enable / ListUsers
                                     ↘   CloudWatch Logs（監査・アクセス, 90日）
[Cognito User Pool (U5 所有)] ← ImportValue で U3 が issuer/audience 参照
```

## 2. スタック関係・クロススタック参照
- **U5 スタック（iyf-infra）**: Cognito UserPool/Client/Groups を所有し、`iyf-${Stage}-UserPoolId` / `-UserPoolClientId` を **Export**（実装済）。
- **U3 スタック（iyf-backend-api, SAM）**: 上記を **`Fn::ImportValue`** で参照して JWT オーソライザと IAM(UserPool ARN)を構成。
- 依存方向: **U5 → U3**（U5 を先にデプロイ/更新）。Export を Import が参照するため、U5 の当該 Export は削除・名称変更不可（U3 が依存）。

## 3. デプロイ順序（Phase 2）
```
1. U5 infra 更新（Phase 2 調整: Admin MFA 強制・Token 有効期限明示・必要なら初期admin投入）
   └ 既存 Export（UserPoolId/ClientId）を維持
2. U3 backend-api 更新（sam build && sam deploy）
   ├ GSI-status 追加（Posts/Notices/Inquiries）※オンライン更新（GSI 追加はテーブル更新）
   ├ AdminFunction 追加 + 管理ルート + JWT オーソライザ
   └ 既存レコードへ status/updated_at_epoch バックフィル（1回スクリプト）
3. 初期 admin アカウント作成（U5/運用手順: AdminCreateUser + admin グループ + MFA 設定）
4. U2 admin-web デプロイ（後続ユニット）
```
- **GSI 追加の注意**: DynamoDB の GSI 追加はテーブルごとに逐次（同時に複数 GSI を1回で追加不可な制約に留意）。CloudFormation では通常1回のデプロイで1 GSI/テーブル。Posts/Notices/Inquiries は別テーブルのため並行可。
- **バックフィル**: 既存レコードに `status`/`updated_at_epoch`（Posts/Notices）、`status`（Inquiries）を付与しないと GSI に載らない。移行済み記事(U4)も対象。Build&Test 段でスクリプト実行。

## 4. ロールバック / 段階リリース
- Phase 2 は Phase 1 公開サイトに影響を与えない（公開ルート・PublicFunction は不変）。
- 問題時は AdminFunction/管理ルートを無効化しても公開系は稼働継続（疎結合）。
- GSI 追加は後方互換（既存クエリに影響なし）。

## 5. 環境・設定
- Stage: `prod` 単独（Phase 1 踏襲, Q-I4=A）。
- 追加環境変数: `USER_POOL_ID`（ImportValue）。`ALLOWED_ORIGINS` に admin-web オリジンを追加。
- 秘密情報: SSM SecureString（既存プレフィックス `/iyf/${Stage}/`）。

## 6. 監視
- AdminFunction 専用ロググループ（90日）。既存 AlarmTopic（U5）へ認可失敗・エラー率アラームを追加（U5/監視標準）。

## 7. トレーサビリティ
- 参照: `infrastructure-design-phase2.md`, `../nfr-design/logical-components-phase2.md`, `iyf-infra/template.yaml`, `iyf-backend-api/template.yaml`
- 依存: `inception/application-design/unit-of-work-dependency.md`（Phase 2: U5→U3→U2）
