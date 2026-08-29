# 業務ロジックモデル (Business Logic Model) — U3 backend-api / Phase 2 管理系

管理系（auth + admin API）の処理フロー・メソッド署名・主要シーケンス。技術非依存（実装は Python）。
参照: `business-rules-admin.md`, `domain-entities-admin.md`, Phase 1 の `business-logic-summary.md`。

---

## モジュール構成（Phase 2 追加分）

```
src/
  auth/                    # ★ 新規モジュール
    models.py              # UserProfile, Principal, InviteRequest, Role
    repository.py          # UserProfileRepository (DynamoDB)
    cognito.py             # Cognito 連携 (AdminCreateUser/Group/Disable/Enable)
    service.py             # AuthService (認可・招待・ユーザー管理・プロフィール完了)
  content/service.py       # ★ 管理メソッド追加 (create/update/delete/setStatus, list_all)
  calendar/service.py      # ★ 管理メソッド追加 (create/update/delete)
  contact/service.py       # ★ 管理メソッド追加 (list_all, get, update_status)
  common/
    auth.py                # ★ 本実装化: require_role / require_owner / Principal
    audit.py               # ★ 既存を管理系イベントで利用 (BR-AUDIT)
  handlers/
    public.py              # 既存（公開系）
    admin.py               # ★ 新規: 認証必須ハンドラ（ルーティング→認可→service）
```

---

## 認可の共通前段（common/auth.py 本実装化）

概念シグネチャ:
```
Principal{ sub: str, role: 'admin'|'editor', groups: list[str] }

get_principal(event) -> Principal | None     # JWT claim(検証済) から復元
require_authenticated(event) -> Principal     # None なら 401
require_role(principal, *allowed) -> None     # role 不一致なら 403
require_owner(principal, resource_author_id) -> None  # admin は素通り, editor は sub 一致必須, 不一致 403
```

- **BR-AUTH-02**: 署名・失効検証は API Gateway オーソライザが済ませている前提。ここではロール/オーナー判定に集中。
- 全 admin ハンドラは「`require_authenticated` → `require_role`（必要な操作の許可ロール）→（対象ありなら）`require_owner`」の順で通す。

---

## AuthService（新規）

| メソッド | 認可 | 署名（概念） | 処理概要 |
|---|---|---|---|
| inviteEditor | Admin | `invite_editor(actor, email) -> UserSummary` | email 正規化→重複検査→Cognito AdminCreateUser（招待メール+仮PW）→editor グループ追加→UserProfile stub 作成(status=active, displayName=pending)→監査 |
| completeProfile | 認証済(本人) | `complete_profile(principal, display_name) -> UserProfile` | 初回ログイン後、本人が displayName 設定→pending 解除。以後投稿可（BR-USER-02） |
| listUsers | Admin | `list_users() -> list[UserSummary]` | UserProfile 一覧（role/status/displayName/email/createdAt） |
| setUserStatus | Admin | `set_user_status(actor, user_id, status) -> void` | active/disabled 切替。disabled→Cognito AdminDisableUser。自己/最後のadmin 無効化は 409（BR-USER-04） |
| ensureProfile | 内部 | `ensure_profile(principal) -> UserProfile` | 各 admin リクエスト前に profile を取得。未存在なら stub 補完（Cognito 直作成 admin 対策） |
| requirePostable | 内部 | `require_postable(profile) -> void` | displayName pending なら 409（投稿不可, BR-USER-02） |

### 招待フロー（inviteEditor）シーケンス
```
Admin(admin-web) -> AdminAPI: POST /admin/users/invite {email}
AdminAPI -> auth.require_role(admin)
AuthService -> validate/normalize email; 重複?→409
AuthService -> Cognito.AdminCreateUser(email, 一時PW, DesiredDeliveryMediums=EMAIL)
AuthService -> Cognito.AdminAddUserToGroup(sub, 'editor')
AuthService -> UserProfileRepo.put(stub: role=editor,status=active,displayName=null,invitedBy=actor)
AuthService -> audit('user.invite', target=sub)
AdminAPI -> 201 {UserSummary}
（Cognito が招待メール+仮PW送付。ユーザーは初回ログイン→仮PW変更→completeProfile）
```

### 初回ログイン→プロフィール完了
```
Editor: Cognito Hosted UI/SDK でログイン（仮PW→新PW, MFA設定は Admin のみ必須:SECURITY-12）
Editor(admin-web) -> AdminAPI: PUT /admin/me/profile {displayName}
AuthService.complete_profile: displayName 検証(1..40)→UserProfile 更新(pending解除)
-> 200 {UserProfile}
```

---

## ContentService（管理メソッド追加）

公開系（Phase 1）はそのまま。以下を追加（Post/Notice 共通の形）:

| メソッド | 認可 | 署名（概念） | 主なルール |
|---|---|---|---|
| createPost | Admin/Editor(要profile) | `create_post(principal, PostInput) -> PostId` | authorId=sub, authorDisplayName=snapshot, 初期 draft。status=published 指定時は BR-STATE-02 検証 |
| updatePost | Admin(全)/Editor(自) | `update_post(principal, postId, PostInput) -> void` | require_owner。存在しない→404、他人→403 |
| deletePost | Admin(全)/Editor(自) | `delete_post(principal, postId) -> void` | require_owner（Q1=A: Editor は自記事削除可） |
| setPostStatus | Admin(全)/Editor(自) | `set_post_status(principal, postId, status) -> void` | BR-STATE 遷移。published 化は必須項目検証。publishedAt 補完 |
| listPostsAdmin | Admin/Editor | `list_posts_admin(principal, filter?) -> Page` | BR-LIST-02: Admin=全draft+published / Editor=自draft+全published |
| getPostAdmin | Admin/Editor | `get_post_admin(principal, postId) -> PostDetail` | draft も取得可（Editor は自draft or published のみ、他人draft は 404 相当） |
| createNotice/updateNotice/deleteNotice/setNoticeStatus/listNoticesAdmin/getNoticeAdmin | 同上 | Post に準ずる | お知らせ（authorId あり・オーナー制適用） |

- **PostInput**: `{title, bodyRichText, status, publishedAt?}`。bodyRichText はサニタイズ（BR-VALID-02）。

### 記事公開シーケンス（setPostStatus: draft→published）
```
Editor -> AdminAPI: PUT /admin/posts/{id}/status {status:'published'}
AdminAPI -> require_authenticated -> require_role(admin|editor)
ContentService.get(id): 無→404
ContentService: require_owner(principal, post.authorId)   # editor は自記事のみ
ContentService: require_postable(profile)                 # displayName pending→409
ContentService: BR-STATE-02 検証（title/body 非空）→不足 422
ContentService: post.status=published; publishedAt=now(JST) if unset
Repo.save(post); audit('post.publish', target=id)
-> 公開系一覧/詳細に即時反映
```

---

## CalendarService（管理メソッド追加, Q3=B）

| メソッド | 認可 | 署名（概念） | ルール |
|---|---|---|---|
| createEvent | Admin/Editor | `create_event(principal, EventInput) -> EventId` | 所有者概念なし（BR-OWN-03）。作成者は監査記録 |
| updateEvent | Admin/Editor | `update_event(principal, eventId, EventInput) -> void` | 誰でも任意 Event を編集可（共有カレンダー） |
| deleteEvent | Admin/Editor | `delete_event(principal, eventId) -> void` | 同上。存在しない→404 |
| （listEvents/getEvent は公開系 Phase 1 のまま） | Public | — | 公開閲覧は既存 |

- **EventInput**: `{title(1..80), type, startAt, endAt?, place?, note?}`。type∈{practice,game,other}。

---

## ContactService（管理メソッド追加, US-14 / Admin のみ）

公開系 `submitInquiry`（Phase 1）はそのまま。管理系を追加:

| メソッド | 認可 | 署名（概念） | ルール |
|---|---|---|---|
| listInquiries | Admin | `list_inquiries(principal, status?) -> Page` | 受信日時(receivedAt)降順。status で絞り込み可 |
| getInquiry | Admin | `get_inquiry(principal, inquiryId) -> InquiryDetail` | 詳細（clientMeta 含む・PII最小表示） |
| updateInquiryStatus | Admin | `update_inquiry_status(principal, inquiryId, status) -> void` | status∈{new,in_progress,done}。updatedBy=sub, updatedAt=now |

- Editor はアクセス不可（BR-AUTH-05 → 403）。

---

## Admin ハンドラ（handlers/admin.py 新規）

- API Gateway（AdminApiGateway, 認証必須）からのルーティング入口。
- 共通処理: correlationId 付与 → `require_authenticated` → ルート別 `require_role` → service 呼び出し → 例外を HTTP へマッピング（401/403/404/409/422/429）→ 監査ログ。
- 想定ルート（契約詳細は Infra/Code 段階で確定。api-documentation.md へ追補）:
  ```
  POST   /admin/posts                     createPost
  GET    /admin/posts                      listPostsAdmin
  GET    /admin/posts/{id}                  getPostAdmin
  PUT    /admin/posts/{id}                  updatePost
  DELETE /admin/posts/{id}                  deletePost
  PUT    /admin/posts/{id}/status           setPostStatus
  （notices も同型）
  POST   /admin/events / GET / PUT / DELETE  calendar 管理
  GET    /admin/inquiries                    listInquiries
  GET    /admin/inquiries/{id}               getInquiry
  PUT    /admin/inquiries/{id}/status        updateInquiryStatus
  POST   /admin/users/invite                 inviteEditor (admin)
  GET    /admin/users                        listUsers (admin)
  PUT    /admin/users/{id}/status            setUserStatus (admin)
  PUT    /admin/me/profile                   completeProfile (self)
  ```

---

## 主要ビジネスシナリオ / エッジケース

- **他人の記事を編集しようとする Editor** → `require_owner` で 403（IDOR 防止, SECURITY-08）。
- **プロフィール未完了(displayName pending)のまま投稿** → 409（BR-USER-02）。
- **draft を公開せず放置** → 公開系には出ない。管理系一覧に残る（作成者/Admin のみ可視）。
- **published を取り下げ（→draft）** → 公開サイトから即時消滅（BR-STATE-04）。
- **無効化された Editor の既存記事** → 表示継続（authorDisplayName スナップショット, BR-USER-04/BR-OWN-02）。
- **最後の admin を無効化/自己無効化** → 409（ロックアウト防止, BR-USER-04）。
- **重複 email 招待** → 409（BR-VALID-03）。
- **カレンダー Event の同時編集** → 共有前提。後勝ち（楽観ロックは NFR/Infra で要否判断。小規模のため既定は後勝ち＋監査）。
