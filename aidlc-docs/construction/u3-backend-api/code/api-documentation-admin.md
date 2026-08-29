# API Documentation（管理系 / Phase 2）— U3 backend-api

すべて **認証必須**（`Authorization: Bearer <Cognito access token>`）。API Gateway JWT オーソライザ→アプリ層 require_role/require_owner。
ロール: `admin`=全操作 / `editor`=ブログ・お知らせ・カレンダー（自リソースのみ編集/削除/公開）。
エラー: 401 未認証 / 403 権限外・他人リソース / 404 不存在 / 409 状態衝突 / 422 業務ルール違反 / 429 レート超過。

## ブログ（editor 自記事 / admin 全件）
| メソッド | パス | ロール | 説明 |
|---|---|---|---|
| POST | `/admin/posts` | admin,editor | 作成（要 profile 完了）。body: `{title, body, category?, status}` |
| GET | `/admin/posts?status=&cursor=` | admin,editor | 一覧（draft含む）。editor は自draft+全published |
| GET | `/admin/posts/{id}` | admin,editor | 詳細（他人draftは404秘匿） |
| PUT | `/admin/posts/{id}` | admin(全)/editor(自) | 更新 |
| DELETE | `/admin/posts/{id}` | admin(全)/editor(自) | 削除 |
| PUT | `/admin/posts/{id}/status` | admin(全)/editor(自) | 公開/非公開。body: `{status}` |

## お知らせ（ブログと同型）
`/admin/notices`（POST/GET）, `/admin/notices/{id}`（GET/PUT/DELETE）, `/admin/notices/{id}/status`（PUT）

## カレンダー（共有編集: オーナー制なし）
| メソッド | パス | ロール | 説明 |
|---|---|---|---|
| POST | `/admin/events` | admin,editor | 作成。body: `{title, description?, location?, event_date, status}` |
| GET | `/admin/events?status=&cursor=` | admin,editor | 一覧（draft含む） |
| PUT | `/admin/events/{id}` | admin,editor | 更新（誰でも任意イベント可） |
| DELETE | `/admin/events/{id}` | admin,editor | 削除 |

## 問い合わせ（Admin のみ）
| メソッド | パス | ロール | 説明 |
|---|---|---|---|
| GET | `/admin/inquiries?status=` | admin | 一覧（status 絞り込み可・受信日時降順） |
| GET | `/admin/inquiries/{id}` | admin | 詳細 |
| PUT | `/admin/inquiries/{id}/status` | admin | 対応状況更新。body: `{status: 未対応/対応中/対応済}` |

## ユーザー / 自プロフィール
| メソッド | パス | ロール | 説明 |
|---|---|---|---|
| POST | `/admin/users/invite` | admin | 編集者招待。body: `{email}`。Cognito 招待メール+仮PW |
| GET | `/admin/users` | admin | 管理ユーザー一覧 |
| PUT | `/admin/users/{id}/status` | admin | 有効/無効。body: `{status: active/disabled}`。自己/最後のadmin不可 |
| PUT | `/admin/me/profile` | 認証済(本人) | 初回ログイン後の displayName 設定。body: `{display_name}` |

## 認証フロー（概要）
1. 招待（admin）→ Cognito が招待メール+仮パスワード送付
2. 編集者が Cognito でログイン（仮PW→新PW、admin は MFA/TOTP）
3. `PUT /admin/me/profile` で displayName 設定（→ 投稿可能に）
4. `Authorization: Bearer <access>` で各管理APIを呼び出し
