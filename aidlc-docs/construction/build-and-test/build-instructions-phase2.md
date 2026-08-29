# Build Instructions（Phase 2 管理CMS）

対象3リポジトリの Phase 2 追加分をビルド/検証する。Phase 1 手順（`build-instructions.md`）を前提に、差分を示す。

## 前提
- **Python 3.13**（backend/infra）、**Node 20+/npm**（admin-web）、任意で **AWS SAM CLI**（infra/backend の validate/deploy）。
- OS: Windows(PowerShell) / macOS / Linux いずれも可。

## 1. U3 backend-api（管理API 追加）
```bash
cd iyf-backend-api
python -m venv .venv && . .venv/Scripts/activate   # mac/linux: . .venv/bin/activate
pip install -e ".[dev]"        # bleach 追加済み
python -c "import bleach; print('bleach', bleach.__version__)"   # allowlist サニタイズ確認
# SAM テンプレート検証（SAM CLI がある場合）
sam validate --lint            # GSI-status×4 / AdminFunction / JWT authorizer
```
- **期待**: 依存解決成功、`sam validate` OK（CLI 無しの場合はスキップ、デプロイ時に検証）。

## 2. U5 infra（Cognito token 有効期限）
```bash
cd iyf-infra
sam validate --lint            # UserPoolClient の TokenValidity 追加を検証
```
- **期待**: 検証 OK。変更は UserPoolClient のみ（Export 不変）。

## 3. U2 admin-web（管理SPA・新規）
```bash
cd iyf-admin-web
npm install
cp .env.example .env           # 実接続時は値を設定。未設定ならダミーモード
npm run typecheck              # tsc -b --noEmit
npm run build                  # dist/ 生成
npm run dev                    # ローカル確認（ダミーモード, http://localhost:5174）
```
- **期待**: 型チェック 0 エラー、ビルド成功（dist 生成）。

## ビルド成果物
- backend: SAM ビルド成果物（`.aws-sam/`）※デプロイ時
- infra: SAM テンプレート（`iyf-infra/template.yaml`）
- admin-web: `iyf-admin-web/dist/`（静的資材、U5 S3/CloudFront へ配信）

## トラブルシュート
- **admin-web ビルドで esbuild エラー**: `npm install` を再実行（postinstall で platform binary を取得）。
- **backend で bleach import 不可**: `pip install -e ".[dev]"` を再実行（requirements/pyproject に固定済み）。
- **sam validate が UserPoolId Import で失敗**: U5 スタックを先にデプロイし Export を用意（`iyf-<stage>-UserPoolId`）。
