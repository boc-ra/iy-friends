# 業務ルール (Business Rules) — U3 backend-api / Phase 2 管理系

Phase 1 の `business-rules.md`（公開読取・問い合わせ送信）を拡張する、管理系(auth + admin API)のルール定義。
確定回答: Q1=A, Q2=A, Q3=B, Q4=A, Q5=B, Q6=A, Q7=A, Q8=A（`plans/u3-backend-api-phase2-functional-design-plan.md`）。

技術非依存。DynamoDB キー設計・Cognito 具体設定は NFR/Infrastructure Design（U3/U5）で確定する。

---

## BR-AUTH: 認可の基本方針（SECURITY-06/08/12）

- **BR-AUTH-01（deny-by-default）**: 全 Admin API は「認証必須 + サーバー側認可」。トークンが無い/無効なら `401`、権限不足なら `403`（fail-closed）。
- **BR-AUTH-02（トークン検証の責務分担）**: 署名・失効・`aud`/`iss`・有効期限の検証は **API Gateway JWT オーソライザ(Cognito)** が実施。U3 は検証済み claim（`sub`, `cognito:groups`）を信頼し、**ロール認可とオーナー認可**を担当する（`src/common/auth.py` の枠組みを本実装化）。
- **BR-AUTH-03（ロール source）**: ロールは Cognito グループ（`admin` / `editor`）を正とする。U3 の `User.role` は表示・整合用のミラー。判定は claim のグループを優先。
- **BR-AUTH-04（未知ロール）**: claim にグループが無い/未知のロールは権限なし扱い（`403`）。

### 認可マトリクス（確定）
凡例: ✓=可 / —=不可 / 「自」=自分が作成したものに限る

| 操作 | Admin | Editor |
|---|:--:|:--:|
| ブログ 作成 (createPost) | ✓ | ✓ |
| ブログ 編集 (updatePost) | ✓(全件) | ✓(自) |
| ブログ 削除 (deletePost) | ✓(全件) | ✓(自) ※Q1=A |
| ブログ 公開/非公開 (setPostStatus) | ✓(全件) | ✓(自) ※Q2=A |
| お知らせ 作成/編集/削除/公開 | ✓(全件) | ✓(自) |
| カレンダー 作成/編集/削除 | ✓ | ✓ ※Q3=B（所有者概念なし=全件可） |
| 問い合わせ 一覧/詳細/状態更新 | ✓ | — |
| ユーザー招待/一覧/無効化 | ✓ | — |
| 管理系一覧（draft含む）取得 | ✓(全draft) | ✓(自draft + 全published) ※下記 BR-LIST-02 |

- **BR-AUTH-05（Editor スコープ）**: Editor が操作できるのは **ブログ・お知らせ・カレンダー**のみ。問い合わせ管理・ユーザー管理は Admin 専用（`403`）。
- **BR-AUTH-06（IDOR 防止, SECURITY-08）**: Editor の update/delete/setStatus は、対象リソースの `authorId` が呼び出し元 `sub` と一致する場合のみ許可。不一致は `403`（存在は秘匿せず 403 で明示。ただし存在しない ID は `404`）。

---

## BR-OWN: オーナーシップ（記事・お知らせ）

- **BR-OWN-01**: Post/Notice は作成時に `authorId = 呼び出し元 sub`、`authorDisplayName = User.displayName のスナップショット` を確定保存する。
- **BR-OWN-02**: `authorDisplayName` はスナップショット。以後 User の改名・無効化・削除があっても記事表示は安定（BR-USER-04 と整合）。
- **BR-OWN-03（カレンダー例外）**: Event は**所有者フィールドを持たない**（`domain-entities.md`：作成者は監査ログで追跡）。したがってカレンダーは「共有のチーム予定」とみなし、**カレンダー権限を持つ Admin/Editor は誰でも任意の Event を編集・削除可能**。作成者・更新者は監査ログ(BR-AUDIT)で追跡する。
  - > 設計判断（上書き可）: 個別オーナー制にしたい場合は Event に `authorId` を追加し BR-AUTH-06 を適用する。

---

## BR-STATE: 下書き/公開の状態遷移（Post/Notice）

状態: `draft`（下書き） / `published`（公開）。初期は `draft`。

- **BR-STATE-01（遷移）**: 許可される遷移は `draft → published`（公開）と `published → draft`（非公開化＝取り下げ）。同状態への再設定は冪等（no-op）。
- **BR-STATE-02（公開時の必須項目）**: `published` へ遷移するには `title`（1..120）と `bodyRichText`（サニタイズ後に非空）が必須。欠落時は `422`。
- **BR-STATE-03（publishedAt）**: `draft → published` で `publishedAt` 未設定なら「現在時刻(JST)」を設定（公開予約なし, Q-F5=A）。`published → draft` にしても `publishedAt` は保持（再公開時に更新するかは setPostStatus の引数で制御。既定は保持）。
- **BR-STATE-04（公開範囲の一貫性）**: 公開系 API（Phase 1）は `is_public()`（=published）判定を維持。`published → draft` にした瞬間、公開サイトの一覧・詳細から即座に消える（詳細は `404`）。
- **BR-STATE-05（権限）**: Editor は自分の Post/Notice に限り公開/非公開化が可能（Q2=A）。Admin は全件可。

---

## BR-LIST: 一覧 API の可視範囲（Q7=A）

- **BR-LIST-01（公開/管理の分離）**: 公開系 `GET /posts`・`/notices`（認証不要）は **published のみ**。管理系 `GET /admin/posts`・`/admin/notices`（認証必須）は **draft+published** を状態バッジ付きで返す。公開系には draft を一切出さない。
- **BR-LIST-02（Editor の draft 可視範囲）**: 管理系一覧で、
  - **Admin** は全ユーザーの draft を閲覧可。
  - **Editor** は「**自分の draft**」＋「**全ユーザーの published**」を閲覧可（他人の未公開の下書きは見えない＝未公開作業の秘匿 + BR-AUTH-06 のオーナー制と整合）。
  - > 設計判断（上書き可）: 小規模運用で「Editor も全 draft を閲覧可」にしたい場合は本ルールを緩める。
- **BR-LIST-03（並び順・ページング）**: 既存踏襲。published は `publishedAt` 降順・10件/頁（Q-F6=A）。管理系は `createdAt`/`updatedAt` 降順を許容（draft は publishedAt を持たないため）。

---

## BR-USER: ユーザー・招待・無効化（US-15/16, Q4=A/Q5=B/Q6=A）

- **BR-USER-01（招待方式）**: `inviteEditor(adminId, email)` は Cognito `AdminCreateUser` を呼び、**招待メール＋仮パスワード**を送付。作成ユーザーを **editor グループ**へ追加。U3 は DynamoDB に **User プロファイルの stub**（`userId=Cognito sub`, `email`, `role=editor`, `status=active`, `displayName=null(pending)`, `invitedBy=adminId`, `createdAt`）を作成。
  - 招待できるのは **Admin のみ**（BR-AUTH-05）。招待対象ロールは editor 固定（admin の増設はブートストラップ運用: U5 infra で初期 admin を投入）。
- **BR-USER-02（displayName 確定=初回ログイン, Q5=B）**: 招待された本人は初回ログインで仮パスワードを変更し、**自分の displayName を設定**する（`completeProfile(sub, displayName)`）。`displayName` 未設定（pending）のユーザーは **記事/お知らせを作成/公開できない**（`409`：プロフィール未完了）。設定後に投稿可能。
  - `displayName`: 1..40 文字、必須、サニタイズ（SECURITY-05）。
- **BR-USER-03（一覧）**: `listUsers()` は Admin のみ。role/status/displayName/email/createdAt を返す（PII 最小: email は管理目的で保持・表示）。
- **BR-USER-04（無効化, Q6=A）**: `setUserStatus(adminId, userId, disabled)` は Admin のみ。Cognito 側でユーザーを**無効化（AdminDisableUser）**し、U3 の `User.status=disabled` を設定。以後ログイン不可・既存トークンは失効ポリシーに従い早期に無効。
  - **既存の公開記事はそのまま表示**（`authorDisplayName` スナップショット保持, BR-OWN-02）。下書きの凍結は行わない（Q6=A）。
  - 自分自身の無効化は不可（`409`：ロックアウト防止）。最後の有効な admin の無効化も不可。
- **BR-USER-05（再有効化）**: `setUserStatus(..., active)` で Cognito 再有効化 + `status=active`。displayName は保持。

---

## BR-VALID: 入力検証（SECURITY-05, 既存踏襲）

- **BR-VALID-01**: 全 Admin 入力はスキーマ検証（型・長さ・形式）。`PostInput{title(1..120), bodyRichText, status, publishedAt?}`、`NoticeInput` 同様、`EventInput{title(1..80), type∈{practice,game,other}, startAt, endAt?, place(0..80), note(0..500)}`、`InquiryStatus∈{new,in_progress,done}`。
- **BR-VALID-02（リッチテキスト・サニタイズ）**: `bodyRichText` は保存時・表示時に allowlist サニタイズ（XSS 防止）。許可タグ以外は除去。
- **BR-VALID-03（email）**: 招待 email は形式検証・正規化（小文字化・trim）。既に存在する email の再招待は `409`（重複）または再送として扱う（既定: 重複エラー）。

---

## BR-AUDIT: 監査ログ（SECURITY-13/14, Q8=A）

- **BR-AUDIT-01（保存先）**: 管理系ミューテーション（create/update/delete/setStatus/invite/setUserStatus/completeProfile）は **CloudWatch Logs へ構造化ログ**として記録（専用テーブルは作らない=低コスト, NFR-COST）。
- **BR-AUDIT-02（記録項目）**: `correlationId`, `timestamp(JST)`, `actorId(sub)`, `actorRole`, `action`（例: `post.publish`）, `targetType`, `targetId`, `result(success/deny/error)`, （必要に応じ）`changedFields` の**キー名のみ**。**本文・PII・秘密情報は出力しない**（SECURITY-03）。
- **BR-AUDIT-03（認可失敗も記録）**: `401/403` の認可失敗もログ・アラート対象（SECURITY-14）。
- **BR-AUDIT-04（fail-closed）**: 監査ログ書き込みは best-effort（ログ失敗で業務処理は止めないが、書き込み失敗自体を error ログに残す）。

---

## エラー方針（既存踏襲, SECURITY-15）

| 状況 | HTTP | 備考 |
|---|:--:|---|
| 未認証 | 401 | トークン無/無効 |
| 権限不足・他人リソース(IDOR) | 403 | Editor が他記事を操作 等 |
| 対象不存在 | 404 | 存在秘匿（draft も公開系からは 404） |
| 入力検証失敗 | 422 | 型/長さ/形式/公開必須欠落 |
| 重複・状態衝突（プロフィール未完了/自己無効化/email重複） | 409 | |
| レート超過（招待等） | 429 | 任意 |

- ユーザー向けは汎用メッセージ、詳細はログのみ（fail-closed, SECURITY-15）。
