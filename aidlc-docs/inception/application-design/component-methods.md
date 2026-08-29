# コンポーネント メソッド (Component Methods) — IYフレンズ公式サイト

各サービスの **メソッド署名（高レベル）** と入出力を定義する。
言語表記は概念シグネチャ（実装は Python）。**詳細な業務ルール・バリデーション詳細・データモデルは Construction/Functional Design で確定**する。

凡例: `[Public]`=公開API（認証不要） `[Admin]`=管理API（認証必須） / DTO は暫定名

---

## ContentService（ブログ・お知らせ・静的ページ）

| メソッド | 種別 | 署名（概念） | 目的 |
|---|---|---|---|
| listPosts | [Public] | `listPosts(page, pageSize, archiveMonth?) -> Page<PostSummary>` | 公開済みブログ記事の一覧/アーカイブ取得 |
| getPost | [Public] | `getPost(postId) -> PostDetail` | 公開済み記事の詳細取得（非公開は404） |
| listNotices | [Public] | `listNotices(page, pageSize) -> Page<NoticeSummary>` | 公開済みお知らせ一覧 |
| getNotice | [Public] | `getNotice(noticeId) -> NoticeDetail` | 公開済みお知らせ詳細 |
| createPost | [Admin] | `createPost(authorId, PostInput) -> PostId` | 記事作成（下書き/公開） |
| updatePost | [Admin] | `updatePost(actorId, postId, PostInput) -> void` | 記事更新（権限チェック） |
| deletePost | [Admin] | `deletePost(actorId, postId) -> void` | 記事削除 |
| setPostStatus | [Admin] | `setPostStatus(actorId, postId, status) -> void` | 下書き/公開の切替 |
| createNotice / updateNotice / deleteNotice / setNoticeStatus | [Admin] | 上記記事に準ずる | お知らせ管理 |

- **入出力の要点**: `PostInput{ title, bodyRichText, status, publishedAt? }`。本文はWYSIWYG由来のリッチテキスト（サニタイズ必須, SECURITY-05）。
- **PII配慮**: 本文中の氏名は掲載しない運用（DR-05）。表示時のサニタイズも実施。

## CalendarService（活動予定）

| メソッド | 種別 | 署名（概念） | 目的 |
|---|---|---|---|
| listEvents | [Public] | `listEvents(fromDate, toDate) -> List<EventSummary>` | 期間内の公開予定取得 |
| getEvent | [Public] | `getEvent(eventId) -> EventDetail` | 予定詳細 |
| createEvent | [Admin] | `createEvent(actorId, EventInput) -> EventId` | 予定登録 |
| updateEvent | [Admin] | `updateEvent(actorId, eventId, EventInput) -> void` | 予定更新 |
| deleteEvent | [Admin] | `deleteEvent(actorId, eventId) -> void` | 予定削除 |

- `EventInput{ title, startAt, endAt?, type(練習/試合/その他), place?, note? }`

## ContactService（お問い合わせ）

| メソッド | 種別 | 署名（概念） | 目的 |
|---|---|---|---|
| submitInquiry | [Public] | `submitInquiry(InquiryInput, clientMeta) -> InquiryId` | 問い合わせ送信（検証→保存→SES通知） |
| listInquiries | [Admin] | `listInquiries(page, pageSize, status?) -> Page<InquirySummary>` | 履歴一覧 |
| getInquiry | [Admin] | `getInquiry(inquiryId) -> InquiryDetail` | 詳細取得 |
| updateInquiryStatus | [Admin] | `updateInquiryStatus(actorId, inquiryId, status) -> void` | 対応状況更新（未対応/対応済 等） |

- `InquiryInput{ name, email, message }`（型/長さ/形式検証, SECURITY-05）。`clientMeta` はレート制限/スパム対策用。
- 送信先メールは**設定値（後から変更可能）**として保持（CON-03）。SES送信。

## AuthService（認証・認可・アカウント）

| メソッド | 種別 | 署名（概念） | 目的 |
|---|---|---|---|
| authorizeRequest | [Admin横断] | `authorizeRequest(token, requiredRole) -> Principal` | トークン検証＋ロール認可（全AdminAPIの前段） |
| inviteEditor | [Admin] | `inviteEditor(adminId, email) -> void` | 編集者を招待（Cognito招待メール） |
| listUsers | [Admin] | `listUsers() -> List<UserSummary>` | 管理ユーザー一覧 |
| setUserStatus | [Admin] | `setUserStatus(adminId, userId, status) -> void` | 有効/無効化 |
| (Cognito) login/mfa/logout | — | Cognito Hosted UI / SDK に委譲 | ログイン・MFA・ログアウト |

- **認可**: `inviteEditor`/`setUserStatus`/`listUsers` は Admin ロールのみ（SECURITY-06/08）。Editor は投稿系のみ。
- **トークン検証**: 署名・失効・aud/iss をサーバー側で毎回検証（SECURITY-12）。

## BlogMigrationTool（移行）

| メソッド | 種別 | 署名（概念） | 目的 |
|---|---|---|---|
| scrapeSource | batch | `scrapeSource(baseUrl) -> List<RawPost>` | 現行サイトから記事収集 |
| normalize | batch | `normalize(RawPost) -> PostInput` | タイトル/本文/投稿日/著者へ正規化（画像は除外） |
| importPosts | batch | `importPosts(List<PostInput>) -> ImportReport` | ContentService 経由で投入・重複回避 |

---

## 横断的な入出力方針（全サービス共通）
- **入力検証**: 全 API 入力はスキーマ検証（型・長さ・形式・サニタイズ）（SECURITY-05）
- **エラー**: 失敗時は fail-closed、ユーザーには汎用メッセージ、詳細はログのみ（SECURITY-15）
- **ログ**: 相関ID付き構造化ログ、PII/秘密情報は出力しない（SECURITY-03）
- **監査**: 管理系の変更（誰が/いつ/何を）を記録（SECURITY-13/14）

> 注: 具体的なバリデーション条件・状態遷移・データ項目の詳細は Functional Design（ユニット単位）で定義する。
