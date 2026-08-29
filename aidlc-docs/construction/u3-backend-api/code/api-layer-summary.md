# APIレイヤ 要約

`src/handlers/public.py`（API Gateway HTTP API / Lambda proxy）。

- routeKey（例 `GET /posts`）でディスパッチ。
- 各ハンドラ: `parse_body`/`validate`（検証, SECURITY-05）→ `auth.require_public`（公開判定, SECURITY-08）→ サービス → `make_response`。
- `with_error_handling` で全体をラップ（fail-closed・汎用エラー・相関IDログ, SECURITY-15）。
- ページング: base64 不透明カーソル（`_encode_cursor`/`_decode_cursor`）。
- 時刻は JST でハンドラが確定しサービスへ注入（決定性）。
- レスポンスに `X-Content-Type-Options`、許可オリジンのみ CORS。

ルート: GET /posts, /posts/{id}, /notices, /notices/{id}, /events, /events/{id}, POST /contact。
テスト: `test_handlers.py`（404・検証400・成功・セキュリティヘッダ・CORS制限）。
