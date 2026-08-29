# NFR Design Patterns（Phase 2 追補）— U3 backend-api

Phase 1 `nfr-design-patterns.md` を継承し、Phase 2（auth + 管理API）で追加適用するパターンを定義。

---

## 1. セキュリティ・認可パターン（中核）

### 1.1 二層認可（Layered AuthZ, SECURITY-08/12）
```
[Client(admin-web)] --Bearer JWT--> [API Gateway (AdminApi)]
    └ 層1: JWT オーソライザ = 署名/iss/aud/exp/失効 検証（Cognito User Pool）
             │ 検証済 claims(sub, cognito:groups) を context へ
             ▼
        [Lambda handlers/admin.py]
    └ 層2: common/auth.py
        - require_authenticated(event) -> Principal（claim から復元、無ければ 401）
        - require_role(principal, *allowed)（不一致 403）
        - require_owner(principal, resource.authorId)（admin 素通り / editor は sub 一致 / 不一致 403）
```
- **deny-by-default**: 保護ルートは必ず層2ガードを通す。ガード漏れを防ぐため handler 冒頭で必須呼び出し（レビュー観点）。
- **IDOR 防止**: 更新/削除/公開は対象取得後に `require_owner`。存在しない ID は 404、権限外は 403。

### 1.2 MFA / トークンパターン
- Admin グループに **TOTP MFA 必須**（Cognito）。Editor 任意。
- access/id=1h（短命）で失効性、refresh=30d でスマホ再ログイン頻度を抑制。
- 秘密情報（Cognito App Client secret 等）は SSM SecureString/Secrets Manager（平文禁止, SECURITY-12）。

### 1.3 入力・サニタイズ
- 全 Admin 入力 Pydantic 検証（型/長さ/形式）。`bodyRichText` は bleach allowlist サニタイズ（保存時＋表示時, SECURITY-05）。

## 2. データアクセスパターン（DynamoDB, マルチテーブル継承）

### 2.1 Posts / Notices — 管理系一覧
- 既存 `GSI-published`（PK=status(=published), SK=publishedAt desc）は**公開系専用**。
- 追加 **`GSI-status`（PK=status, SK=updatedAt desc）**: 管理系一覧で draft/published を Query。
  - Admin: `status=draft` と `status=published` を各 Query → マージ（updatedAt/publishedAt でソート）、10件/ページ（LastEvaluatedKey カーソル）。
  - Editor: `status=draft` の結果を Lambda 内で `authorId==sub` フィルタ（draft は少数）＋ `status=published` は全件可視（BR-LIST-02）。
- Scan は使わない（一覧は常に Query）。

### 2.2 Users — プロファイル
- PK=userId(sub)。取得は GetItem。
- **email 一意性は Cognito が担保**（AdminCreateUser 重複拒否）。DynamoDB 側 email GSI は当面持たない（コスト/一貫性の単純化）。
- **listUsers**: Users テーブルは ≤10 件のため **Scan 許容**（admin・低頻度）。Phase 1「Scan回避」の限定例外として明記。

### 2.3 Inquiries / Events（既存 GSI 流用）
- Inquiries: 既存 `GSI-status`（status, createdAt desc）で listInquiries（status 絞り込み）をそのまま利用。updateInquiryStatus は GetItem→PutItem。
- Events: 既存 `GSI-date`。管理系 create/update/delete は PK 直アクセス。

## 3. 冪等性・リトライ・信頼性パターン（SECURITY-15）

- **Cognito 操作**（AdminCreateUser/AddUserToGroup/Disable/Enable）: `auth/cognito.py` に隔離。bounded retry（指数バックオフ、上限あり）、例外は業務エラーへマッピング、fail-closed。
- **招待の部分失敗対策**: 「Cognito 作成成功→グループ追加失敗」等の中間失敗に備え、`ensure_profile`/再実行で収束（冪等）。email 重複は 409。
- **監査 best-effort**: 監査ログ書き込み失敗は業務を止めないが error ログに残す（BR-AUDIT-04）。

## 4. 可観測性・監査パターン

- 全 admin ハンドラで相関ID付与→構造化ログ（PIIマスク, SECURITY-03）。
- 監査イベント（create/update/delete/publish/invite/setUserStatus/completeProfile）を CloudWatch Logs へ（actor/role/action/targetType/targetId/result/changedFieldsキー名）。
- 認証失敗(401)/認可違反(403) もログ＋アラート対象（SECURITY-14）。

## 5. レート制限パターン
- AdminApiGateway ステージに既定スロットリング（レート/バースト）。招待は軽い上限。
- ログイン濫用は Cognito 組込（アカウントロック/遅延）。追加 WAF なし（N4=A）。

## 6. 性能パターン
- 管理系は低頻度・小データ。プロビジョンド同時実行なし。管理系 GET はキャッシュしない（最新性優先／認証必須のため CDN キャッシュ対象外）。
