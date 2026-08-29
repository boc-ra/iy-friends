# Unit Test Execution（Phase 2）

## U3 backend-api
```bash
cd iyf-backend-api
pytest -q
```
- **結果（実行確認済み）**: **79 passed**（Phase 1 の 33 + Phase 2 追加 46）。
- Phase 2 の主なテスト:
  - `test_auth.py` — role/owner 判定（PBT含む）、AuthService invite/complete/disable（自己・最後のadmin保護）
  - `test_content_admin.py` — オーナー制（他人記事→403）、公開必須欠落→422、draft 可視範囲
  - `test_calendar_admin.py` / `test_contact_admin.py` — 共有編集、status 絞り込み/更新
  - `test_handlers_admin.py` — 未認証→401、権限外→403、未知ルート→404、正常系
- **カバレッジ方針**: 認可・状態遷移・シリアライズ往復（PBT 部分適用）を重点。

## U2 admin-web
```bash
cd iyf-admin-web
npm run typecheck     # 型検証（実行確認済み: 0 エラー）
npm run build         # ビルド検証（実行確認済み: 成功, 708 modules）
```
- フロントは型チェック＋ビルドを一次検証とする（ユニットテストフレームワークは Phase 2 では未導入。将来 vitest 追加可）。

## U5 infra
- ユニットテストは対象外（IaC）。`sam validate` を検証手段とする（`build-instructions-phase2.md`）。
