# U3 backend-api (Phase 2) — Code Generation Plan（Part 1: Planning）

**ユニット**: U3 backend-api（Phase 2 管理系）／ブラウンフィールド（既存 `iyf-backend-api/` を**その場で修正/追加**、複製禁止）
**ワークスペース**: `C:\Users\syuto\IY FRIENDS\iyf-backend-api`（アプリコード）／ドキュメントは `aidlc-docs/construction/u3-backend-api/code/`
**対象ストーリー**: US-07/09/11/14/15/16/18（管理系・認証）
**設計参照**: functional-design `*-admin.md` / nfr-design `*-phase2.md` / infrastructure-design `*-phase2.md`
**既存規約の踏襲**: Pydantic モデル・`Repository` 基底・routeKey ディスパッチ・`with_error_handling`・pytest+Hypothesis(PBT部分適用)・fail-closed。

**後方互換の原則**: 既存 Phase 1 コード/テストを壊さない。モデル追加フィールドは**任意（デフォルト付き）**。公開系(`handlers/public.py`)は不変。

---

## ステップ一覧（この計画が唯一の実行ソース。各ステップ完了時に [x]）

### 共通レイヤ（common）
- [x] **Step 1**: `src/common/errors.py` 修正 — `ConflictError`(409)・`UnprocessableError`(422) 追加（`__all__` 登録済）。US-18
- [x] **Step 2**: `src/common/auth.py` 修正 — `Principal`、`require_authenticated`/`require_role`/`require_owner`、純粋判定 `is_role_allowed`/`is_owner_allowed`（PBT可）を実装。`require_public` 維持。US-15/18
- [x] **Step 3**: `src/common/db.py` 修正 — `Repository` に `update_item`/`delete`/`scan_all` 追加

### auth モジュール（新規）
- [x] **Step 4**: `src/auth/__init__.py`（新規）
- [x] **Step 5**: `src/auth/models.py`（新規）— `Role`・`UserStatus`・`ProfileState`・`UserProfile`・`InviteRequest`・`CompleteProfileRequest`・`SetUserStatusRequest`
- [x] **Step 6**: `src/auth/cognito.py`（新規）— `CognitoClient`（注入可能）: admin_create_user/add_to_group/disable/enable。重複=Conflict、失敗=CognitoError
- [x] **Step 7**: `src/auth/repository.py`（新規）— `UserProfileRepository`: get/put_profile/update_profile_fields/list_all(scan)/count_active_admins
- [x] **Step 8**: `src/auth/service.py`（新規）— `AuthService`: invite_editor/complete_profile/list_users/set_user_status（自己・最後のadmin保護）/get_postable_profile/_ensure_profile。監査記録

### content 管理（修正）
- [x] **Step 9**: `content/models.py` — Post/Notice に author_id/created_at/updated_at/updated_at_epoch(任意)追加。`PostInput`/`NoticeInput`/`StatusUpdate`/`admin_summary` 追加
- [x] **Step 10**: `content/repository.py` — item に status(常時)付与＋_strip_none。`save`/`delete_*`/`list_by_status`（GSI-status）追加
- [x] **Step 11**: `content/service.py` — 管理メソッド create/update/delete/set_status/get_admin/list_admin（require_owner・BR-STATE公開必須検証・publishedAt補完・Editor draft可視制御・監査）。＋ validation に `sanitize_richtext`（bleach optional）追加
- [x] **Step 12**: `calendar/models.py` — `EventInput`（既存フィールド title/description/location/event_date/status に整合）・`event_admin_summary` 追加
- [x] **Step 13**: `calendar/repository.py` — status(常時)付与、`save`/`delete_event`/`list_by_status`（GSI-status, SK=event_date_epoch）追加
- [x] **Step 14**: `calendar/service.py` — create/update/delete/list_admin/get_admin（共有編集・オーナー制なし・監査）
- [x] **Step 15**: `contact/models.py` — `Inquiry.to_summary`/`updated_at`/`updated_by` 追加、`InquiryStatusUpdate` 追加
- [x] **Step 16**: `contact/repository.py` — `get_inquiry`/`list_by_status`（GSI-status）/`update_status` 追加
- [x] **Step 17**: `contact/service.py` — list_inquiries/get_inquiry/update_inquiry_status（Admin限定は handler）

### API レイヤ（新規ハンドラ）
- [x] **Step 18**: `src/handlers/admin.py`（新規）— routeKey ディスパッチ（23ルート）+ `require_authenticated`→ルート別 `require_role`→service。JST 注入・カーソル/パス補助

### IaC（修正）
- [x] **Step 19**: `template.yaml` — Posts/Notices/Events/Inquiries に `GSI-status` 追加、`AdminFunction`（IAM: 各テーブルCRUD＋cognito-idp[UserPool ARN限定]＋SSM、USER_POOL_ID env）、`HttpApi` に Cognito JWT オーソライザ（issuer/audience=ImportValue）、CORS に PUT/DELETE/authorization。※requirements/pyproject に bleach 追加

### データ移行（新規・バックフィル）
- [x] **Step 20**: `migration/backfill_status.py`（新規）— Posts/Notices に `updated_at_epoch` 補完（Events/Inquiries は既存属性で自動掲載のため対象外）。冪等・dry-run 対応

### テスト（全 79 passed）
- [x] **Step 21**: `tests/test_auth.py` — role/owner 判定（PBT含む）、AuthService invite/complete/disable（自己・最後のadmin保護）
- [x] **Step 22**: `tests/test_content_admin.py` — create/update/delete/set_status、Editor オーナー制、公開必須→Unprocessable、draft 可視範囲
- [x] **Step 23**: `tests/test_calendar_admin.py`・`tests/test_contact_admin.py` — 共有編集、status 絞り込み/更新
- [x] **Step 24**: `tests/test_handlers_admin.py` — routeKey、未認証→401、権限外→403、正常系（monkeypatch）
- [x] **Step 25**: 既存テスト回帰 — 全既存テスト維持（モデル追加フィールドは任意で後方互換）。79 passed

### ドキュメント
- [x] **Step 26**: `aidlc-docs/construction/u3-backend-api/code/` に Phase 2 サマリ・API doc 生成
- [x] **Step 27**: `iyf-backend-api/README.md` に Phase 2 追記

---

## ストーリー・トレーサビリティ
| ストーリー | 実装ステップ |
|---|---|
| US-07 ブログ投稿/編集/削除/公開 | 9,10,11,18,22 |
| US-09 お知らせ投稿 | 9,10,11,18,22 |
| US-11 カレンダー登録 | 12,13,14,18,23 |
| US-14 問い合わせ管理 | 15,16,17,18,23 |
| US-15 ログイン/認可 | 2,18,24 |
| US-16 編集者招待/無効化 | 5,6,7,8,18,21 |
| US-18 セキュリティ（認可/監査/最小権限） | 1,2,8,11,19 全般 |

## 依存・前提
- **U5 infra**: Cognito UserPool/Client/Groups は構築済（Export 参照）。Admin MFA 強制・Token 有効期限明示・初期admin投入は U5 Phase 2 / 運用（`shared-infrastructure.md` §3b）。本ユニットは Import 参照のみ。
- **テスト方針**: 本ステージではコードとテストを生成。実行（pytest / sam validate）は次の **Build and Test（Phase 2）** で実施（コード生成中に軽く自己検証は行う）。
- **境界**: DynamoDB/Cognito への実接続はテストではスタブ化（副作用隔離）。

## スコープ・規模
- 新規 9 ファイル + 修正 10 ファイル + IaC 1 + 移行 1 + テスト 4〜5 + ドキュメント 3。合計 **27 ステップ**。
- 公開系・データモデルの後方互換を維持（Phase 1 無停止）。

---

**この計画で Part 2（生成）を実行してよいか承認してください。** 変更点があれば「Request Changes」で指定してください。
