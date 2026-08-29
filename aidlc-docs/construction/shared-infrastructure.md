# Shared Infrastructure — 申し送りメモ（U5 infra ユニットで集約）

本メモは、複数ユニット（U1 public-web / U2 admin-web / U3 backend-api）で共有するインフラを、後続の **U5 infra ユニット**で最終集約するための申し送り。U3 Infrastructure Design 時点の前提を記録する。

> 注: U3 は backend-api 側の論理→物理対応を確定済み。共有部分の「最終的なリソース所有・命名・IaC集約」は U5 で確定する。

---

## 1. 共有インフラ候補

| 共有リソース | 使う側 | 想定 | 所有(最終) |
|---|---|---|---|
| **CloudFront** | U1(公開), U2(管理) | 静的配信・キャッシュ・HTTPセキュリティヘッダ付与（SECURITY-04） | U5 |
| **S3** | U1, U2, U4(移行) | 静的ホスティング資材・画像。パブリックアクセスブロック（SECURITY-09） | U5 |
| **Cognito User Pool** | U2(管理UI), U3(API認可) | 管理者/編集者認証、MFA、パスワードポリシー | U5（U3はImport参照） |
| **API Gateway ドメイン/ステージ** | U3, U1/U2から呼び出し | prod ステージ、スロットリング、アクセスログ | U3定義 / U5でドメイン紐付け |
| **ドメイン (Route53/ACM)** | 全体 | Phase1はCloudFrontデフォルトドメイン（費用0, NFR-DOM-01）。将来独自ドメイン（NFR-DOM-02） | U5 |
| **CloudWatch（集中ログ/アラート）** | 全体 | ログ保持90日、セキュリティアラート（SECURITY-14） | U5で標準化 |

## 2. U3 → U5 への具体的申し送り事項

1. **Cognito**: U3 API は Cognito JWT オーソライザを利用。User Pool/Client は U5 で作成し、U3 は ARN/ID を Import（またはSSM Parameter経由で参照）。MFA(管理者必須)・パスワードポリシー(8文字以上・漏洩チェック)を U5 で設定（SECURITY-12）。
2. **CloudFront セキュリティヘッダ**: HTML配信の CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy は CloudFront（U5）で付与（SECURITY-04）。API(JSON)側は U3 が最小限付与。
3. **S3 パブリックアクセスブロック**（SECURITY-09）と、外部スクリプトの SRI（SECURITY-13）は U1/U5 で担保。
4. **アクセスログ**（SECURITY-02）: CloudFront標準ログ / API Gateway アクセスログを CloudWatch/S3 に集約（U5で保存先標準化）。
5. **ドメイン**: Phase1 は `*.cloudfront.net`（0円）。独自ドメイン `iy-o-endan.com` 引き継ぎ or 新規は U5 で後付け可能な構成に。
6. **IaC集約**: U3 は AWS SAM。共有リソースは U5 側 IaC（SAM/CDK いずれか、U5で決定）で管理し、クロススタック参照（Export/Import or SSM Parameter）で連携。

## 3. 未確定（U5 で決定）

- 共有リソースの IaC ツール（U3=SAM に合わせるか、CDK 等にするか）
- クロススタック連携方式（CloudFormation Export/Import vs SSM Parameter）
- 独自ドメイン取得/引き継ぎの時期と手順
- CloudFront セキュリティヘッダの具体ポリシー値（CSP の許可オリジン等）

## 3b. Phase 2 追記（U3 Phase 2 Infrastructure Design 時点）

U3 Phase 2（管理API）が U5 に依存/申し送る事項:

1. **Cognito 参照方式（確定）**: U3 は `Fn::ImportValue: iyf-${Stage}-UserPoolId` / `-UserPoolClientId` を JWT オーソライザ・IAM(UserPool ARN)で参照。→ **これら Export は削除・改名しないこと**（U3 が依存）。
2. **Admin MFA 強制（U5-1=A で確定）**: 現状 `MfaConfiguration: OPTIONAL` を**維持**（editor 任意）。Admin の MFA 必須は **admin-web ログインフローで強制**（admin グループは初回 TOTP 登録必須・未設定は管理画面不可）。追加インフラなし。将来サーバー側強制が必要なら PreTokenGeneration Lambda へ後方互換で移行可。
3. **Token 有効期限の明示（U5 Phase 2 で対応・確定）**: `UserPoolClient` に `AccessTokenValidity=1`(hours) / `IdTokenValidity=1`(hours) / `RefreshTokenValidity=30`(days) + `TokenValidityUnits` を明示（N3=A）。
4. **初期 admin ブートストラップ（U5/運用）**: 最初の管理者は招待元が存在しないため、U5 デプロイ後の運用手順（AdminCreateUser + admin グループ追加 + 初回 MFA 設定）で投入。手順を U5 側 runbook に記載。
5. **admin-web オリジン**: CloudFront(U5) で管理配信を用意する場合、その本番オリジンを U3 の `ALLOWED_ORIGINS`（CORS）へ反映（相互調整）。
6. **監視**: AdminFunction の認可失敗/エラー率アラームを U5 の `AlarmTopic` に接続（監視標準化）。

## 4. トレーサビリティ

- 参照: `u3-backend-api/infrastructure-design/infrastructure-design.md`, `deployment-architecture.md`
- 関連要件: NFR-DOM-01/02, NFR-OPS-03, SECURITY-02/04/09/12/13/14
- 依存: `inception/application-design/unit-of-work-dependency.md`（U3→U5→U1 のPhase1順）
