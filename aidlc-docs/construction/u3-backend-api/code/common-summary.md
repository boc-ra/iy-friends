# common レイヤ 要約

共通基盤（`src/common/`）。全モジュールが依存する横断機能。

| ファイル | 役割 | 主なSECURITY |
|---|---|---|
| config.py | 環境変数＋SSM(SecureString)、JST、テーブル名、ページサイズ、CORS許可 | 12 |
| logging.py | 構造化JSONログ・相関ID・PIIマスク（mask_pii） | 03 |
| errors.py | 例外型、with_error_handling（fail-closed/汎用メッセージ）、make_response（CORS/ヘッダ） | 15/09/08/04 |
| validation.py | parse_body/validate(Pydantic)/sanitize_text/clamp_limit | 05 |
| auth.py | 公開/認証判定、Cognito claim 復元（Phase2で本格化） | 08 |
| db.py | DynamoDB基底（Query/GetItem/PutItem、限定リトライ、Scan回避） | 06 |
| audit.py | 重要変更の監査ログ | 13 |

テスト: `tests/test_common.py`（PBT: sanitize_text/clamp_limit）。PBTが clamp_limit の上限未丸めを検出→修正。
