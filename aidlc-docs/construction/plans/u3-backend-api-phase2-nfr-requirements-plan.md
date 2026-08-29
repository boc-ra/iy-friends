# U3 backend-api (Phase 2) — NFR Requirements Plan & Questions

**対象**: U3 backend-api Phase 2（auth + 管理API）の非機能要件。
**前提（Phase 1 で確定・再質問しない）**: 東京単一リージョン / Lambda+DynamoDB On-Demand / 低コスト最優先（月数百円）/ PITR有効 / Security Baseline 全適用 / 監視は CloudWatch 最低限 / 応答目標 概ね1秒。技術スタック（Python サーバーレス・Cognito・SES）確定済み。
**Phase 2 で新たに決める NFR**: 認証まわりのポリシー（MFA・トークン寿命・レート制限）。以下のみを確認します。

---

## Part 1 — 設計プラン（チェックボックス）

- [x] MFA 適用範囲（Admin のみ / Editor も）の確定（SECURITY-12）→ N1=A
- [x] MFA 方式（TOTP / SMS）の確定 → N2=A
- [x] トークン/セッション寿命（Cognito access/id/refresh）の確定 → N3=A
- [x] 認証・管理系のレート制限/スロットリング方針の確定（SECURITY-11）→ N4=A
- [x] nfr-requirements.md（Phase 2 追補）/ tech-stack-decisions.md（追補）の生成

---

## Part 2 — 質問

### Question N1 — MFA の適用範囲（SECURITY-12）
SECURITY-12 は「管理者 MFA」。編集者(Editor)にも MFA を必須にしますか？

A) Admin は MFA 必須 / Editor は任意（推奨・SECURITY-12 の最小充足。10名規模で運用負担少）

B) Admin・Editor とも MFA 必須（最も厳格。全員が認証アプリ設定を要）

C) 全員 MFA 任意（最小限。※SECURITY-12 の「管理者MFA」を満たさない可能性）

X) Other（[Answer]: の後に記述）

[Answer]: A （推奨既定を適用：ユーザーが「完了」時に空欄のため。変更可）

### Question N2 — MFA の方式
MFA の手段は？（SMS はコスト・到達性の懸念、TOTP は無料・アプリ必要）

A) TOTP（Google Authenticator 等の認証アプリ）のみ（推奨・無料・安全）

B) SMS のみ（アプリ不要だが SMS 送信コスト・SIM 依存）

C) TOTP + SMS の両方を選択可

X) Other（[Answer]: の後に記述）

[Answer]: A （推奨既定を適用：空欄のため。変更可）

### Question N3 — トークン/セッション寿命（Cognito）
スマホ中心の管理画面での再ログイン頻度に影響します。

A) 標準（access/id = 1時間 / refresh = 30日）。30日はスマホで再ログインが少なく快適（推奨）

B) 短め・厳格（access/id = 1時間 / refresh = 1日）。毎日再ログイン。機密性重視

C) 長め（access/id = 1時間 / refresh = 90日）。利便性最優先

X) Other（[Answer]: の後に記述）

[Answer]: A （推奨既定を適用：空欄のため。変更可）

### Question N4 — レート制限・スロットリング（SECURITY-11）
管理系・認証まわりの濫用対策は？

A) API Gateway の既定スロットリング + Cognito 組込のブルートフォース対策（アカウントロック/遅延）で充足。招待は Admin 操作のため軽い上限のみ（推奨・低コスト・追加実装最小）

B) 招待・状態更新など個別エンドポイントに厳格なカスタムレート制限を追加（WAF/独自カウンタ）

X) Other（[Answer]: の後に記述）

[Answer]: A （推奨既定を適用：空欄のため。変更可）

---

**回答が終わったら「done」等でお知らせください。** 空欄・曖昧があれば追加確認します。問題なければ nfr-requirements（Phase 2 追補）と tech-stack-decisions（追補）を生成します。
