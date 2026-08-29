# Code Generation Summary（Phase 2 管理系）— U3 backend-api

ブラウンフィールド（既存 `iyf-backend-api/` をその場修正/追加）。**全 79 テスト passed**。公開系(Phase 1)は不変・後方互換維持。

## 生成/修正ファイル

### 新規（Created）
- `src/auth/__init__.py` / `models.py` / `cognito.py` / `repository.py` / `service.py` — 認可・招待・ユーザー管理・Cognito 連携
- `src/handlers/admin.py` — 管理API ルーター（23ルート、認証必須）
- `migration/backfill_status.py` — GSI-status バックフィル（Posts/Notices の updated_at_epoch）
- `tests/test_auth.py` / `test_content_admin.py` / `test_calendar_admin.py` / `test_contact_admin.py` / `test_handlers_admin.py`

### 修正（Modified）
- `src/common/errors.py` — `ConflictError`(409) / `UnprocessableError`(422)
- `src/common/auth.py` — `Principal`、`require_authenticated`/`require_role`/`require_owner`、純粋判定 `is_role_allowed`/`is_owner_allowed`（PBT対象）
- `src/common/db.py` — `Repository.update_item`/`delete`/`scan_all`
- `src/common/validation.py` — `sanitize_richtext`（bleach allowlist、未導入時はエスケープにフォールバック）
- `src/content/models.py` — Post/Notice に author_id/created_at/updated_at/updated_at_epoch（任意）、`PostInput`/`NoticeInput`/`StatusUpdate`/`admin_summary`
- `src/content/repository.py` — GSI-status 対応（status常時付与・_strip_none）、`save`/`delete_*`/`list_by_status`
- `src/content/service.py` — 管理メソッド（create/update/delete/set_status/get_admin/list_admin、オーナー認可・状態遷移・draft可視制御・監査）
- `src/calendar/models.py` `repository.py` `service.py` — `EventInput`、共有編集の CRUD、GSI-status
- `src/contact/models.py` `repository.py` `service.py` — `InquiryStatusUpdate`、`list_by_status`/`get`/`update_status`
- `template.yaml` — GSI-status×4、AdminFunction、Cognito JWT オーソライザ、CORS(PUT/DELETE/authorization)
- `requirements.txt` / `pyproject.toml` — `bleach==6.4.0`
- `iyf-backend-api/README.md` — Phase 2 追記

## 主要な設計の実装対応
| 決定 | 実装 |
|---|---|
| 二層認可（SECURITY-08） | 層1=APIGW JWT オーソライザ / 層2=`common/auth` require_role・require_owner |
| Editor オーナー制（Q1/Q2=A・IDOR） | `require_owner` を update/delete/set_status に適用。他人記事→403 |
| Editor スコープ（Q3=B） | admin ルートで require_role(admin,editor)=ブログ/お知らせ/カレンダー、require_role(admin)=問い合わせ/ユーザー |
| 招待（Q4=A・Q5=B） | `AuthService.invite_editor`（AdminCreateUser+editorグループ+stub）、`complete_profile`（初回displayName） |
| 無効化（Q6=A） | `set_user_status`（Cognito Disable+status）、自己/最後のadmin保護、既存記事はスナップショットで保持 |
| draft 一覧（Q7=A・BR-LIST-02） | 管理系 `GSI-status`。Editorは自draft+全published、Adminは全draft |
| 監査（Q8=A） | `common/audit.record_change`（CloudWatch 構造化ログ、PII非出力） |
| 状態遷移（BR-STATE） | 公開時 title/body 必須検証（Unprocessable）、publishedAt 補完、非公開化で即時取り下げ |

## テスト観点（79 passed）
- 認可: role/owner の許可・拒否、空ロール deny-by-default、PBT（editor は sub 一致時のみ許可）
- 招待/ユーザー: 重複email→Conflict、profile pending→Conflict、自己/最後のadmin無効化→Conflict
- content: Editor 他人記事→Forbidden、公開必須欠落→Unprocessable、draft 可視範囲、published_at 補完
- calendar: 共有編集（他人イベントも編集可）、draft 含む一覧
- contact: status 絞り込み/全件降順、状態更新（Admin）
- handlers: 未認証→401、権限外→403、未知ルート→404、正常系200

## 次段（Build and Test / Phase 2）への申し送り
- `sam validate` / `sam build` / `sam deploy`（本環境に SAM CLI 無し、構文は Phase 1 と同一スタイル）
- **U5 依存**: Cognito Export（UserPoolId/ClientId）を Import。Admin MFA 強制・Token 有効期限明示・初期adminブートストラップは U5/運用（`shared-infrastructure.md` §3b）
- **バックフィル**: デプロイ後に `python -m migration.backfill_status`（Posts/Notices）を実行
- 結合テスト: 管理フロー（招待→初回ログイン→投稿→公開→問い合わせ管理）の e2e は U2 admin-web 完成後
