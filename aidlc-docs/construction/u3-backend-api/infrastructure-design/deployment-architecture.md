# Deployment Architecture — U3 backend-api（IYフレンズ）

IaC: **AWS SAM**（Q-I1=A）。環境: **本番 `prod` のみで開始**（Q-I4=A）。リージョン: ap-northeast-1（東京）。

---

## 1. デプロイ構成図（論理）

```
                        [ 利用者 / 管理者・編集者 ]
                                  │ HTTPS(TLS1.2+)
                                  ▼
                   [ CloudFront ]  ← 静的配信/キャッシュ（U1/U5で構築）
                                  │
                                  ▼
                   [ API Gateway (HTTP API, stage: prod) ]
                    - スロットリング / アクセスログ
                    - Cognito JWT オーソライザ（管理系）
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
     [Lambda: content]    [Lambda: calendar]   [Lambda: contact]
             │                    │                 │   │
             ▼                    ▼                 ▼   ▼
        [DynamoDB          [DynamoDB          [DynamoDB   [SES]
         Posts/Notices]     Events]            Inquiries]  (通知)
                                                    │
                                                    ▼
                                          [SSM Parameter Store]
                                           (SecureString: SES設定 等)

     横断: [Cognito UserPool]（認証） / [CloudWatch Logs+Alarms]（保持90日）
     IAM: 各Lambdaに最小権限ロール
```

## 2. SAM テンプレート構成（方針）

- `template.yaml`（SAM）に以下を定義:
  - `AWS::Serverless::Api`（HTTP API, stage=prod, スロットリング, アクセスログ, CORS制限, Cognitoオーソライザ）
  - `AWS::Serverless::Function` × モジュール（content/calendar/contact）＋ common は共有レイヤ or 共通コード
  - `AWS::DynamoDB::Table` × 5（PITR/SSE/On-Demand/GSI）
  - `AWS::Cognito::UserPool` ＋ Client（MFA/パスワードポリシー）※U5と重複する場合はU5に集約しU3はImport
  - IAMロール（最小権限, Policyをテーブル/操作単位で付与）
  - CloudWatch LogGroup（保持90日, RetentionInDays: 90）＋ Alarm（認証/認可失敗）
  - SSM Parameter（SecureString）参照
- ランタイム: `python3.13`。依存はロックファイル固定（SECURITY-10）。

## 3. デプロイ手順（概要, 詳細は Build and Test）

1. `sam build`（依存解決・ビルド）
2. `sam deploy --guided`（初回）／以降 `sam deploy`（prod スタック）
3. デプロイ前にセキュリティ/依存スキャン（CI）
4. スモークテスト（主要エンドポイント疎通）

## 4. 環境戦略（Q-I4=A）

- **初期**: `prod` 単一スタックのみ。サーバーレスは従量課金のため、環境を増やしても固定費はほぼ増えない。
- **将来**: 必要時に `dev` スタックを同一テンプレートから追加（パラメータでステージ名・リソース名接尾辞を切替）。

## 5. ロールバック / 変更管理

- SAM/CloudFormation のスタック更新は変更セットで確認可能。失敗時は自動ロールバック。
- DynamoDB は PITR により最大35日前まで復元可能（データ面のロールバック）。

## 6. 後段への申し送り

- **U5 infra ユニット**へ: CloudFront/S3/独自ドメイン/共有Cognito の集約（`shared-infrastructure.md` 参照）
- **Code Generation**へ: SAM `template.yaml` 実体、Lambda実装、依存ロックファイル、CIの脆弱性スキャン/SBOM
- **Build and Test**へ: `sam build`/`deploy`、スモーク/統合テスト手順
