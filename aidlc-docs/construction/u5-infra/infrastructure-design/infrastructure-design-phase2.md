# Infrastructure Design（Phase 2 追補）— U5 infra

Phase 1 `infrastructure-design.md` を継承。Phase 2（認証仕上げ）で `iyf-infra` に加える変更を定義。
反映: U5-1=A（MFA は admin-web フローで強制、`MfaConfiguration: OPTIONAL` 維持）。

---

## 1. Phase 2 の変更点（差分のみ）

| # | 変更 | リソース | 内容 |
|---|---|---|---|
| 1 | **Admin MFA 強制方式** | UserPool / admin-web | `MfaConfiguration: OPTIONAL` を維持（editor 任意, N1=A）。**admin グループの MFA 必須は admin-web ログインフローで強制**（初回 TOTP 登録を必須化。未設定は管理画面に入れない）。Cognito Advanced Security(ENFORCED) が異常検知を補完 |
| 2 | **トークン有効期限の明示** | UserPoolClient | `AccessTokenValidity: 1`(hours) / `IdTokenValidity: 1`(hours) / `RefreshTokenValidity: 30`(days) + `TokenValidityUnits`（N3=A） |
| 3 | **初期 admin ブートストラップ** | 運用(runbook) | 最初の管理者を投入（AdminCreateUser + admin グループ + 初回 MFA）。CFN リソース化せず runbook 手順に（1回・手動） |

- **不変（維持）**: UserPool の TOTP(SOFTWARE_TOKEN_MFA)・招待制(AllowAdminCreateUserOnly)・PasswordPolicy・AdvancedSecurity ENFORCED、admin/editor グループ、Export（UserPoolId/UserPoolClientId）。
- **U3 依存契約**: `iyf-${Stage}-UserPoolId` / `-UserPoolClientId` Export は**削除・改名しない**（U3 が `Fn::ImportValue` 参照）。

## 2. UserPoolClient（変更後イメージ）
```yaml
  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref UserPool
      ClientName: !Sub "iyf-${Stage}-admin-web"
      GenerateSecret: false
      ExplicitAuthFlows:
        - ALLOW_USER_SRP_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      PreventUserExistenceErrors: ENABLED
      # Phase 2: トークン有効期限を明示（N3=A）。
      TokenValidityUnits:
        AccessToken: hours
        IdToken: hours
        RefreshToken: days
      AccessTokenValidity: 1
      IdTokenValidity: 1
      RefreshTokenValidity: 30
```
- admin-web は **SRP 直叩き（Amplify Auth / cognito SDK）** を想定 → Hosted UI 非使用のため `CallbackURLs`/`AllowedOAuthFlows` は不要。

## 3. MFA 強制フロー（admin-web, U2 実装）
```
admin ログイン(USER_SRP_AUTH)
  └ Cognito: パスワード認証 → （MFA 未設定なら）MFA_SETUP チャレンジ or アプリ判定
  └ admin-web: ユーザーが admin グループ かつ MFA 未登録 → TOTP 登録画面を強制
       - associateSoftwareToken → verifySoftwareToken → setUserMFAPreference(SOFTWARE_TOKEN_MFA=preferred)
  └ 完了後のみ管理画面へ遷移
editor は MFA 任意（スキップ可）
```
> enforcement はアプリ層（U2）。サーバー側の追加強制が必要になった場合は PreTokenGeneration Lambda（U5-1 選択肢B）へ後日移行可能（後方互換）。

## 4. セキュリティ対応（Phase 2）
| SECURITY-ID | 対応 |
|---|---|
| SECURITY-12 | admin MFA(TOTP) 強制（admin-web フロー）＋ AdvancedSecurity ENFORCED（漏洩PW/異常検知）＋ 短命アクセストークン(1h) |
| SECURITY-08 | 招待制・グループ(admin/editor)によるロール source。API 認可は U3（JWT オーソライザ + role/owner） |
| SECURITY-14 | 認証異常は Cognito Advanced Security + CloudWatch。U3 認可失敗アラームは AlarmTopic 連携（監視標準） |

## 5. コスト
- 変更は Cognito 設定のみ（Lambda 追加なし=A の利点）。MAU≤10 無料枠内、SMS 不使用 → **増分ほぼ 0 円**。

## 6. トレーサビリティ
- 反映回答: U5-1=A、N1/N2/N3（U3 nfr-requirements-phase2）
- 参照: `iyf-infra/template.yaml`、`../../shared-infrastructure.md` §3b、`../../u3-backend-api/infrastructure-design/infrastructure-design-phase2.md`
