# NFR Requirements（Phase 2 追補）— U3 backend-api（IYフレンズ）

Phase 1 の `nfr-requirements.md` を継承したうえで、**Phase 2（管理系 auth + admin API）で追加・具体化する NFR** を定義する。
Phase 1 の決定（東京単一リージョン / Lambda+DynamoDB On-Demand / PITR / 低コスト最優先 / 監視最低限 / 応答 概ね1秒 / Security Baseline 全適用）はそのまま有効。
反映した回答: N1=A, N2=A, N3=A, N4=A（`../../plans/u3-backend-api-phase2-nfr-requirements-plan.md`。ユーザー「完了」時に空欄だったため推奨既定を適用、変更可）。

---

## 1. 認証・認可ポリシー（新規・Phase 2 の中核）

| NFR-ID | 要件 | 決定/根拠 |
|---|---|---|
| **NFR-U3-AUTH-01（MFA範囲）** | **Admin は MFA 必須 / Editor は任意** | N1=A。SECURITY-12「管理者MFA」を充足。10名規模で運用負担を抑制。Cognito のグループ/リスクベースで Admin へ MFA 強制 |
| **NFR-U3-AUTH-02（MFA方式）** | **TOTP（認証アプリ）** | N2=A。無料・SMSコスト/到達性問題を回避。Cognito Software Token MFA |
| **NFR-U3-AUTH-03（トークン寿命）** | access/id = **1時間** / refresh = **30日** | N3=A。スマホ中心 CMS の再ログイン頻度を抑えつつ、アクセストークンは短命で失効性確保 |
| **NFR-U3-AUTH-04（ブルートフォース）** | Cognito 組込のアカウントロック/試行遅延を利用 | SECURITY-12。追加実装なし |
| **NFR-U3-AUTH-05（サーバー側認可）** | 全 Admin API は deny-by-default + ロール/オーナー認可（IDOR防止） | SECURITY-08 / functional-design `business-rules-admin.md` BR-AUTH |
| **NFR-U3-AUTH-06（トークン検証責務）** | 署名/失効/aud/iss/期限は API Gateway JWT オーソライザ、U3 はロール/オーナー判定 | 二重責務の明確化 |

## 2. レート制限・濫用対策（SECURITY-11）

| NFR-ID | 要件 | 決定/根拠 |
|---|---|---|
| **NFR-U3-RATE-01** | AdminApiGateway に既定スロットリング（バースト/レート上限）を設定 | N4=A。低コスト・追加実装最小 |
| **NFR-U3-RATE-02** | 招待(inviteEditor)は Admin 操作のため軽い上限のみ（連打防止） | 濫用リスク低。WAF/独自カウンタは非導入 |
| **NFR-U3-RATE-03** | ログイン濫用は Cognito 側で対処（NFR-U3-AUTH-04） | — |

## 3. セキュリティ（Phase 2 で有効化される項目）

Phase 1 で「要件として明記・Phase 2で本格適用」としていた管理系項目を、本 Phase で実装対象として確約:

| SECURITY-ID | Phase 2 U3 での適用 |
|---|---|
| SECURITY-06 | Lambda 実行ロール最小権限に **Cognito 管理操作（AdminCreateUser/AddUserToGroup/Disable/Enable）** を対象限定で追加。ワイルドカード禁止 |
| SECURITY-08 | 管理系 認証必須 + サーバー側ロール検証 + オブジェクトレベル認可（IDOR防止）。CORS はオリジン限定（admin-web） |
| SECURITY-11 | 認可ロジックは `common/auth.py` に集約。管理系スロットリング（NFR-U3-RATE-01） |
| SECURITY-12 | Cognito 認証・Admin MFA(TOTP)・秘密情報は SSM/Secrets Manager・ブルートフォース対策 |
| SECURITY-13 | 管理系ミューテーション（投稿/公開/状態/招待/無効化）を監査ログ化（actor/timestamp/action/target） |
| SECURITY-14 | 認証失敗・認可違反をログ/アラート。ログ保持 ≥90日、アプリは自ログ削除不可 |

## 4. 性能・スケーラビリティ（Phase 1 継承 + 管理系）

| NFR-ID | 要件 |
|---|---|
| NFR-U3-PERF-01（継承） | 管理系 API も通常時 概ね1秒以内（p50 目安、SLAなし）。管理系は低頻度アクセス |
| NFR-U3-SCALE-01（継承） | Lambda + DynamoDB On-Demand。管理系は書き込み中心だが低頻度で追加キャパシティ不要 |
| NFR-U3-PERF-P2-01 | 管理系一覧（draft含む）クエリは status/authorId のアクセスパターンを GSI 等で効率化（詳細は Infra/NFR Design） |

## 5. コスト（Phase 2 の増分）

| NFR-ID | 要件 |
|---|---|
| NFR-U3-COST-P2-01 | **Cognito**: 想定 MAU ≤ 10。無料利用枠（月間アクティブユーザー無料枠）内で実質 0 円。SMS を使わない（TOTP）ため SMS 課金なし |
| NFR-U3-COST-P2-02 | 監査は CloudWatch Logs のみ（監査専用テーブルなし, Q8=A）。ログ量は管理操作のみで小 |
| NFR-U3-COST-P2-03 | 追加 Lambda/API は同一構成に相乗り。Phase 2 でも月数百円規模を維持 |

## 6. 保守性・運用

| NFR-ID | 要件 |
|---|---|
| NFR-U3-MNT-P2-01 | 認可ロジックを `common/auth.py`（require_role/require_owner）に集約し、各ハンドラは薄く |
| NFR-U3-MNT-P2-02 | Cognito 連携は `auth/cognito.py` に隔離（テスト時はスタブ化。副作用の分離） |
| NFR-U3-MNT-P2-03 | PBT 部分適用（継続）: 認可判定（ロール×オーナーの純粋関数）、状態遷移（draft/published）、シリアライズ往復に property test |

## 7. 後段への申し送り（Infrastructure Design / U5 infra）

- Cognito User Pool / App Client 設定（MFA=Admin必須TOTP、トークン寿命 1h/1h/30d、パスワードポリシー、招待メールテンプレート、AdminApiGateway JWT オーソライザ）→ **U5 infra Infrastructure Design**
- 管理系 DynamoDB アクセスパターン（UserProfile の email 逆引き GSI、Post/Notice の status/authorId クエリ）→ **NFR Design / Infrastructure Design**
- 初期 admin アカウントのブートストラップ手順 → U5 infra

## 8. トレーサビリティ

- 参照要件: SECURITY-06/08/11/12/13/14, FR-10/14/19, NFR-COST-01, NFR-OPS-03
- 参照機能設計: `../functional-design/business-rules-admin.md`, `business-logic-model-admin.md`, `domain-entities-admin.md`
- 反映回答: N1=A, N2=A, N3=A, N4=A
