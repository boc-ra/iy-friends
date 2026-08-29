# 技術スタック決定（Phase 2 追補）— U3 backend-api

Phase 1 `tech-stack-decisions.md` を継承。Phase 2（管理系 auth）で追加/確定する技術選定のみ記す。

---

## 継承（Phase 1 で確定・変更なし）
- 言語/実行: **Python + AWS Lambda**
- API: **Amazon API Gateway (HTTP API)**（公開系 PublicApiGateway に加え、Phase 2 で **AdminApiGateway**）
- データ: **DynamoDB（On-Demand, PITR）**
- メール: **Amazon SES**（問い合わせ通知・Cognito 招待メール配信）
- IaC: **AWS SAM**（U5 infra）
- テスト: pytest + Hypothesis（PBT 部分適用）

## Phase 2 追加の技術決定

| 領域 | 決定 | 根拠 |
|---|---|---|
| 認証基盤 | **Amazon Cognito User Pool** | 要件確定（FR-10/14, SECURITY-12）。マネージドで低コスト・MFA/招待/ロック組込 |
| ロール管理 | **Cognito Groups**（`admin` / `editor`） | claim(`cognito:groups`) をロール source に（BR-AUTH-03）。IAM 連携不要でシンプル |
| MFA | **Software Token MFA（TOTP）**、Admin グループに必須 | N1=A/N2=A。無料・SMS課金回避 |
| トークン | access/id=1h, refresh=30d | N3=A |
| 認可（APIGW側） | **JWT オーソライザ**（Cognito User Pool を issuer に） | 署名/失効/aud/iss/期限検証を委譲（NFR-U3-AUTH-06） |
| 認可（アプリ側） | 自前 `common/auth.py`（require_role / require_owner） | ロール/オーナー（IDOR防止, SECURITY-08） |
| Cognito 操作 SDK | **boto3 cognito-idp**（AdminCreateUser / AdminAddUserToGroup / AdminDisableUser / AdminEnableUser） | 招待・無効化（BR-USER）。`auth/cognito.py` に隔離 |
| リッチテキスト サニタイズ | **bleach**（allowlist）※Phase 1 で content 導入済みなら踏襲 | XSS 防止（SECURITY-05, BR-VALID-02） |
| 監査 | **CloudWatch Logs 構造化ログ**（専用ライブラリ不要、`common/audit.py`） | Q8=A・低コスト |
| CORS | admin-web オリジン限定 | SECURITY-08 |

## 新規 Python 依存（想定）
- `boto3`（既存: Cognito 操作を追加利用）
- `bleach`（サニタイズ。Phase 1 未導入なら追加）
- 追加の重量級ライブラリは導入しない（JWT 検証は APIGW オーソライザに委譲するためアプリ側の JWT ライブラリは不要）

## 非選択（今回見送り）
- SMS MFA（コスト・SIM 依存）
- WAF / 独自レート制限（N4=A：APIGW 既定 + Cognito 組込で充足）
- 監査専用 DynamoDB テーブル（Q8=A）
- サードパーティ IdP 連携（自前 Cognito で十分）
