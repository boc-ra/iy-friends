# Unit Test Execution — IYフレンズ Phase 1

## 1. backend + migration（iyf-backend-api）
```bash
cd iyf-backend-api
. .venv/Scripts/activate
pytest -q
```
- **期待**: **33 tests pass, 0 failures**（U3の24 ＋ 移行9）
- **内訳**: `test_common` / `test_content` / `test_calendar` / `test_contact` / `test_handlers` / `test_migration`
- **PBT（部分適用）**: Hypothesis による純粋関数・シリアライズ往復。※過去に `clamp_limit` の上限未丸めをPBTが検出→修正済み
- **カバレッジ（任意）**: `pip install pytest-cov && pytest --cov=src --cov=migration`

### 失敗時
1. 出力の失敗テストを特定
2. 対象コードを修正
3. `pytest -q` を再実行して全green

## 2. public-web（iyf-public-web）
```bash
cd iyf-public-web
npm run typecheck        # 型チェック（実質のユニット検証）
```
- 現状、UIの明示的ユニットテストは未同梱（軽量方針）。必要なら Vitest + Testing Library を追加可能。
- `data-testid` を全インタラクティブ要素へ付与済み（E2E/自動化向け）。

## 注記
- 本ドキュメント作成環境では backend の pytest=33 passed を確認済み。public-web は Node 未導入のため型チェック/ビルドは利用者環境で実施。
