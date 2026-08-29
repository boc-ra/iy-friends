# Build Instructions — IYフレンズ Phase 1

対象リポジトリ（ワークスペース直下）:
- `iyf-backend-api/`（U3 バックエンド ＋ U4 移行, Python/SAM）
- `iyf-infra/`（U5 共有インフラ, SAM）
- `iyf-public-web/`（U1 公開フロント, Vite/React/TS）

## 前提ツール
| ツール | バージョン | 用途 |
|---|---|---|
| Python | 3.13 | backend / migration |
| AWS SAM CLI | 最新 | backend / infra デプロイ |
| Docker | 任意 | `sam local` 実行時のみ |
| Node.js | 20 LTS 以上 | public-web |
| AWS CLI | v2（`aws configure` 済み） | デプロイ・移行 |

---

## 1. backend（iyf-backend-api）
```bash
cd iyf-backend-api
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"          # boto3 / pydantic / pytest / hypothesis / moto
sam validate                     # テンプレート検証（AWS認証情報が必要）
sam build                        # Lambda ビルド
```
- **成果物**: `.aws-sam/build/`、`template.yaml`
- **許容される警告**: SAM の region 未指定警告（`--region ap-northeast-1` で解消）

## 2. infra（iyf-infra）
```bash
cd iyf-infra
sam validate
sam build
```
- **成果物**: `.aws-sam/build/`（S3/CloudFront/Cognito/監視）

## 3. public-web（iyf-public-web）
```bash
cd iyf-public-web
npm install
npm run typecheck                # tsc 型チェック
npm run build                    # dist/ に静的ファイル
npm run dev                      # ローカル確認 http://localhost:5173（ダミーデータ）
```
- **成果物**: `dist/`
- **環境変数**: `.env` の `VITE_API_BASE_URL`（未設定ならダミーデータ）

---

## トラブルシューティング
### Python 依存エラー
- 原因: 仮想環境未有効化 / バージョン不一致
- 対処: `.venv` を有効化し `pip install -e ".[dev]"` を再実行

### sam validate/deploy が認証エラー
- 原因: AWS 認証情報未設定
- 対処: `aws configure`（`ap-northeast-1`）。SSOなら `aws sso login`

### npm run build が型エラー
- 原因: TypeScript 型不一致
- 対処: `npm run typecheck` の指摘箇所を修正して再ビルド

### Node 未導入
- 対処: Node.js 20 LTS を導入（本ドキュメント作成環境には未導入のため public-web のビルドは利用者環境で実施）
