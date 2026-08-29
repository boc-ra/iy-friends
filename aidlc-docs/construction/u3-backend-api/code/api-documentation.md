# API Documentation — U3 backend-api（Phase 1 公開API）

ベースURL: `https://{api-id}.execute-api.ap-northeast-1.amazonaws.com/prod`
共通: レスポンスは JSON(UTF-8)。エラーは `{ "error": "<汎用メッセージ>" }`。ヘッダに `X-Content-Type-Options: nosniff`、許可オリジンのみ `Access-Control-Allow-Origin`。

## GET /posts — ブログ一覧
- クエリ: `cursor`（任意, 次ページ用の不透明トークン）
- 200: `{ "items": [ { "post_id","title","author_display_name","category","published_at" } ], "next_cursor": "<token|null>" }`
- 公開(published)のみ・新しい順・10件/ページ

## GET /posts/{id} — ブログ詳細
- 200: Post 全体（`body` 含む）
- 404: 非公開/存在しない（存在秘匿）

## GET /notices — お知らせ一覧
- 200: `{ "items": [ { "notice_id","title","published_at" } ], "next_cursor": ... }`

## GET /notices/{id} — お知らせ詳細
- 200: Notice 全体 / 404

## GET /events — イベント一覧
- 200: `{ "items": [ { "event_id","title","location","event_date" } ], "next_cursor": ... }`
- 公開のみ・日付昇順

## GET /events/{id} — イベント詳細
- 200: Event 全体 / 404

## POST /contact — 問い合わせ送信
- リクエスト: `{ "name": "<1-100>", "email": "<email>", "message": "<1-5000>" }`（すべて必須）
- 201: `{ "status": "accepted", "inquiry_id": "<uuid>", "duplicate": false }`
  - 短時間の重複送信: `{ "status": "accepted", "duplicate": true }`（新規保存なし）
- 400: 入力検証エラー
- 挙動: DB保存を成立させてから SES 同期通知（ベストエフォート。通知失敗でも受付は成立）

## ステータスコード
| コード | 意味 |
|---|---|
| 200/201 | 成功 |
| 400 | 入力検証エラー |
| 404 | 対象なし（非公開含む） |
| 429 | レート制限（API Gateway スロットリング） |
| 500 | サーバーエラー（汎用メッセージ） |
