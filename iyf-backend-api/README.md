# iyf-backend-api（IYフレンズ バックエンド / U3）

ミニバスケットボールチーム「IYフレンズ」サイトのバックエンドAPI。AWS サーバーレス上のモジュラモノリス。
**Phase 1**（公開読み取りAPI＋問い合わせ送信）に加え、**Phase 2**（管理CMS: 認証・投稿管理・編集者招待）を実装。

## 技術スタック
- Python 3.13 / AWS Lambda（arm64）
- API Gateway（HTTP API）／ DynamoDB（On-Demand・PITR・暗号化）／ SES ／ SSM Parameter Store
- IaC: AWS SAM（`template.yaml`）
- 依存: boto3 / pydantic v2（検証）。dev: pytest / hypothesis(PBT) / moto

## ディレクトリ構成
```
src/
  common/     検証・ログ・エラー・設定(SSM)・DynamoDB基盤・認可(role/owner)・監査
  auth/       認可・招待・ユーザー管理・Cognito 連携（Phase 2）
  content/    ブログ・お知らせ（公開読み取り＋管理）
  calendar/   活動予定（公開読み取り＋管理）
  contact/    問い合わせ（保存＋SES同期通知＋管理）
  handlers/   API Gateway ハンドラ（public / admin）
migration/    既存ブログ移行 + GSI-status バックフィル
tests/        unit + PBT（部分適用）
template.yaml AWS SAM
```

## Phase 1 公開API
| メソッド | パス | 概要 |
|---|---|---|
| GET | `/posts` | ブログ一覧（公開・新しい順・10件・カーソル） |
| GET | `/posts/{id}` | ブログ詳細（公開のみ） |
| GET | `/notices` | お知らせ一覧 |
| GET | `/notices/{id}` | お知らせ詳細 |
| GET | `/events` | イベント一覧（日付昇順） |
| GET | `/events/{id}` | イベント詳細 |
| POST | `/contact` | 問い合わせ送信（name/email/message） |

## セットアップ / テスト
```bash
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## デプロイ（AWS SAM）
```bash
sam build
sam deploy --guided        # 初回。以降は sam deploy
# パラメータ: Stage=prod, AllowedOrigins=https://<公開ドメイン>
```
デプロイ後、SSM に SES 設定を登録（SecureString）:
```bash
aws ssm put-parameter --name /iyf/prod/ses/sender   --type SecureString --value "no-reply@<domain>"
aws ssm put-parameter --name /iyf/prod/ses/notify_to --type SecureString --value "<管理者アドレス>"
```

## セキュリティ（Security Baseline 準拠, コード層）
- 入力検証（Pydantic, SECURITY-05）／ 公開・認可前段（SECURITY-08）
- 構造化ログ・PIIマスク（SECURITY-03）／ 監査ログ（SECURITY-13）
- 最小権限IAM・パラメータ化アクセス（SECURITY-06）／ 秘密情報は SSM（SECURITY-12）
- fail-closed・グローバルエラーハンドラ・汎用メッセージ（SECURITY-15/09）
- 依存固定・脆弱性スキャン（CI）（SECURITY-10）

## Phase 2 管理API（認証必須）
`Authorization: Bearer <Cognito access token>`。ロール: admin=全操作 / editor=ブログ・お知らせ・カレンダー（自リソースのみ編集）。詳細は `aidlc-docs/construction/u3-backend-api/code/api-documentation-admin.md`。

| 区分 | 代表エンドポイント |
|---|---|
| ブログ | `POST/GET /admin/posts`, `GET/PUT/DELETE /admin/posts/{id}`, `PUT /admin/posts/{id}/status` |
| お知らせ | `/admin/notices …`（ブログと同型） |
| カレンダー | `POST/GET /admin/events`, `PUT/DELETE /admin/events/{id}` |
| 問い合わせ(admin) | `GET /admin/inquiries`, `GET /admin/inquiries/{id}`, `PUT /admin/inquiries/{id}/status` |
| ユーザー(admin) | `POST /admin/users/invite`, `GET /admin/users`, `PUT /admin/users/{id}/status` |
| 自プロフィール | `PUT /admin/me/profile`（初回 displayName 設定） |

### Phase 2 デプロイの追加手順
1. **U5 infra（iyf-infra）を先にデプロイ/更新**（Cognito UserPool と `iyf-<stage>-UserPoolId`/`-UserPoolClientId` Export が必要。U3 は `Fn::ImportValue` で参照）
2. `sam build && sam deploy`（AdminFunction・GSI-status・JWT オーソライザが追加される）
3. **GSI-status バックフィル**（既存 Posts/Notices に updated_at_epoch を付与）:
   ```bash
   python -m migration.backfill_status --dry-run   # 確認
   python -m migration.backfill_status             # 実行
   ```
4. 初期 admin アカウントは U5/運用手順で投入（AdminCreateUser + admin グループ + MFA）
5. `AllowedOrigins` に admin-web の本番オリジンを追加

> Cognito の MFA 強制（管理者）・トークン有効期限の明示は U5 infra 側の設定（`aidlc-docs/construction/shared-infrastructure.md` §3b 参照）。
