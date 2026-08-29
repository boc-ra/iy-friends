# ドメインエンティティ (Domain Entities) — U3 backend-api

技術非依存のドメインモデル。属性・型・関連を定義する（DynamoDB のキー設計は Infrastructure/NFR Design で確定）。
設計判断: 著者表示名あり(F1=A)、問い合わせ3ステータス(F2=B)、フォーム=氏名/メール/本文(F3=A)、JST(F4=A)、公開予約なし(F5=A)、10件/頁(F6=A)。

---

## Entity: Post（ブログ記事「スタッフの声」）
| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| postId | string(ULID/UUID) | ● | 一意ID |
| title | string(1..120) | ● | タイトル |
| bodyRichText | richtext/html(sanitized) | ● | 本文（WYSIWYG由来、サニタイズ済） |
| authorId | string | ● | 投稿者(User)への参照 |
| authorDisplayName | string(1..40) | ● | 表示用著者名（F1=A、スナップショット保持） |
| status | enum(draft, published) | ● | 公開状態 |
| publishedAt | datetime(JST) | 公開時● | 公開日時（一覧の並び順キー） |
| createdAt / updatedAt | datetime(JST) | ● | 監査用 |
| source | enum(native, migrated) | ● | 移行データ識別（U4） |

- **関連**: Post *→1 User（authorId）。表示名はスナップショットで保持し、User削除/改名後も記事表示を安定させる。
- **PII**: 本文に子供の氏名を含めない運用（サニタイズは対XSS）。

## Entity: Notice（お知らせ／チーム連絡）
| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| noticeId | string | ● | 一意ID |
| title | string(1..120) | ● | 件名 |
| bodyRichText | richtext(sanitized) | ● | 本文 |
| status | enum(draft, published) | ● | 公開状態 |
| publishedAt | datetime(JST) | 公開時● | 掲載日時 |
| createdAt / updatedAt | datetime(JST) | ● | 監査用 |
| authorId | string | ● | 投稿者参照 |

## Entity: Event（活動予定・カレンダー）
| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| eventId | string | ● | 一意ID |
| title | string(1..80) | ● | 予定名 |
| type | enum(practice練習, game試合, other その他) | ● | 種別 |
| startAt | datetime(JST) | ● | 開始 |
| endAt | datetime(JST) | | 終了（任意） |
| place | string(0..80) | | 場所 |
| note | string(0..500) | | メモ |
| createdAt / updatedAt | datetime(JST) | ● | 監査用 |

- **公開範囲**: すべて公開（一般閲覧可）。個人特定情報は記載しない運用。

## Entity: Inquiry（お問い合わせ）
| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| inquiryId | string | ● | 一意ID |
| name | string(1..60) | ● | 氏名（F3=A） |
| email | string(email形式, ..254) | ● | 連絡先メール |
| message | string(1..2000) | ● | 本文 |
| status | enum(new未対応, in_progress対応中, done対応済) | ● | 対応状況（F2=B、初期=new） |
| receivedAt | datetime(JST) | ● | 受信日時（一覧の並び順） |
| updatedAt | datetime(JST) | ● | 状態更新日時 |
| updatedBy | string | | 最終更新者(User) |
| clientMeta | object(ip, userAgent) | | スパム/レート制御・監査用（PIIとして最小保持） |

## Entity: User（管理ユーザー／Cognito）
| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| userId | string(Cognito sub) | ● | 一意ID |
| email | string(email) | ● | ログインID／招待先 |
| displayName | string(1..40) | ● | 表示名（Post.authorDisplayName の元） |
| role | enum(admin, editor) | ● | 役割 |
| status | enum(active, disabled) | ● | 有効/無効 |
| invitedBy | string | | 招待した管理者 |
| createdAt | datetime(JST) | ● | 作成日時 |

- **実体**: 認証情報は Cognito が保持。U3 はプロファイル（role/displayName/status）を扱う。

---

## エンティティ関連図（テキスト）
```
User(1) ---< Post(*)       (authorId; 表示名はスナップショット)
User(1) ---< Notice(*)     (authorId)
User(admin) ---< User(*)   (invitedBy: 招待関係)
Event: 独立（作成者は監査ログで追跡）
Inquiry: 独立（updatedBy で担当追跡）
```

## 共通の値・制約
- ID: 生成は時刻順ソート可能な ULID を推奨（一覧並びに有利）
- 日時: **JST 固定**（F4=A）。保存は ISO8601（オフセット付き）
- 文字数上限: 上表のとおり（入力検証で強制, SECURITY-05）
- リッチテキスト: 保存時・表示時にサニタイズ（許可タグのallowlist）
