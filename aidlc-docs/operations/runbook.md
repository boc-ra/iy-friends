# 実行手順（Runbook）— IYフレンズ Phase 1 & 2

対象: Windows。ワークスペース = `C:\Users\syuto\IY FRIENDS`
構成: `iyf-public-web`（公開画面）/ `iyf-admin-web`（管理CMS, Phase 2）/ `iyf-backend-api`（API＋移行）/ `iyf-infra`（S3/CloudFront/Cognito/監視）
- **Phase 1**（公開サイト＋問い合わせ）: Path A〜C
- **Phase 2**（管理CMS: ログイン/投稿/問い合わせ管理/招待）: **Path D**

---

## 0. 事前に入れるもの（初回だけ）
| ツール | 用途 | 入手/確認 |
|---|---|---|
| Node.js 20 LTS | 画面(フロント) | https://nodejs.org → `node -v` |
| Python 3.13+ | API/移行 | 既に導入済み（`python --version`） |
| AWS CLI v2 | デプロイ/移行 | `aws --version` → `aws configure`（東京 `ap-northeast-1`） |
| AWS SAM CLI | デプロイ | `sam --version` |
| （任意）Docker | `sam local` を使う時のみ | — |

> **まず画面だけ見たい**なら **Node だけ**でOK（下の Path A）。AWSは後回しで大丈夫。

---

## Path A：ローカルで画面を見る（AWS不要・最短）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-public-web"
npm install
npm run dev
```
→ ブラウザで **http://localhost:5173** を開く。
`VITE_API_BASE_URL` 未設定なので**サンプルデータ**で表示されます（上部に「デモ表示中」帯）。
止めるときは端末で `Ctrl + C`。

---

## Path B：AWSに本番公開（Phase 1）
デプロイ順は **infra → backend → frontend**。

### B-1. 共有インフラ（iyf-infra）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-infra"
sam build
sam deploy --guided
#  Stack Name: iyf-infra-shared-prod / Region: ap-northeast-1 / Stage: prod
#  AlarmEmail は通知が欲しければメール入力（不要なら空Enter）
```
完了後、出力(Outputs)の **CloudFrontDomain / WebBucketName / UserPoolId** を控える。

### B-2. バックエンドAPI（iyf-backend-api）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-backend-api"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                         # 33 passed を確認
sam build
sam deploy --guided
#  Stack Name: iyf-backend-api-prod / Region: ap-northeast-1 / Stage: prod
```
デプロイ後、**問い合わせメール(SES)設定**をSSMに登録（送信元は事前にSESで検証）:
```powershell
aws ssm put-parameter --name /iyf/prod/ses/sender    --type SecureString --value "no-reply@あなたのドメイン"
aws ssm put-parameter --name /iyf/prod/ses/notify_to  --type SecureString --value "受信したい管理者アドレス"
```
出力の **ApiBaseUrl** を控える。

### B-3. CORS 許可（フロントのドメインを許可）
`iyf-backend-api` を CloudFront ドメインからの呼び出し許可で再デプロイ:
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-backend-api"
sam deploy --parameter-overrides "AllowedOrigins=https://<CloudFrontDomain>"
```
（ローカル確認用に `http://localhost:5173` も足す場合はカンマ区切り）

### B-4. フロント公開（iyf-public-web）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-public-web"
# 実APIに繋ぐ
"VITE_API_BASE_URL=<ApiBaseUrl>" | Out-File -Encoding utf8 .env
npm install
npm run build
aws s3 sync dist/ s3://<WebBucketName>/ --delete
# キャッシュ更新（DIST_ID は CloudFront コンソール等で確認）
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```
→ **https://<CloudFrontDomain>/** が公開サイト。

---

## Path C：既存ブログの移行（約339件）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-backend-api"
.\.venv\Scripts\Activate.ps1
pip install requests beautifulsoup4
Copy-Item migration\config.example.toml migration\config.toml
#  → config.toml を現行サイトのURL・CSSセレクタに合わせて編集
python -m migration.run --config migration\config.toml --dry-run --limit 5   # まず確認
python -m migration.run --config migration\config.toml                        # 本投入（冪等・再実行可）
```
投入後、公開サイトのブログ一覧に反映されます（source=migrated / published）。

---

## Path D：管理CMS を公開（Phase 2）
管理者/編集者がログインして投稿・問い合わせ管理・編集者招待を行う画面。**デプロイ順序: U5 → U3 →（backfill）→ 初期admin → U2**。

### D-0. ローカルで先に画面確認（AWS不要）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-admin-web"
npm install
npm run dev      # http://localhost:5174 （ダミーモード。ログイン画面でrole=admin/editorを選び任意メールで入れる）
```

### D-1. 共有インフラを更新（Cognito トークン設定を反映）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-infra"
sam build; sam deploy      # UserPoolClient のトークン有効期限(1h/1h/30d)が反映。Export(UserPoolId/ClientId)は不変
```

### D-2. バックエンドに管理APIを追加デプロイ
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-backend-api"
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"    # bleach を含む
sam build; sam deploy      # AdminFunction / GSI-status×4 / Cognito JWTオーソライザ が追加（U5 Export を Import）
```

### D-3. 既存記事を GSI-status に載せる（1回だけ）
```powershell
python -m migration.backfill_status --dry-run   # 確認
python -m migration.backfill_status             # Posts/Notices に updated_at_epoch を補完
```

### D-4. 初期の管理者を作成（1回だけ）
```powershell
$POOL = aws cloudformation list-exports --query "Exports[?Name=='iyf-prod-UserPoolId'].Value" --output text
aws cognito-idp admin-create-user --user-pool-id $POOL --username "admin@example.com" `
  --user-attributes Name=email,Value="admin@example.com" Name=email_verified,Value=true --desired-delivery-mediums EMAIL
aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --username "admin@example.com" --group-name admin
```
→ 届いた仮パスワードで初回ログイン→新パスワード設定→**認証アプリでMFA登録（管理者は必須）**→表示名を設定。

### D-5. 管理画面を配信（U5 の S3/CloudFront）
```powershell
cd "C:\Users\syuto\IY FRIENDS\iyf-admin-web"
# .env に本番値を設定（VITE_API_BASE_URL / VITE_USER_POOL_ID / VITE_USER_POOL_CLIENT_ID / VITE_AWS_REGION）
npm run build
aws s3 sync dist/ s3://<管理用バケット>/ --delete
aws cloudfront create-invalidation --distribution-id <管理用DIST_ID> --paths "/*"
```
- 管理配信は公開サイトと分けるのが安全（別バケット/ディストリビューション or パス）。
- 管理画面のドメインを U3 の `AllowedOrigins`(CORS) に追加（`sam deploy` のパラメータ）。

### D-6. 動作確認（要点）
- 管理者ログイン→MFA→ダッシュボード表示。編集者を「ユーザー」から招待→被招待者がログイン→表示名設定→記事作成→公開→公開サイトに反映。
- 未対応の問い合わせが「問い合わせ」に出る→状態更新。編集者は問い合わせ/ユーザー画面が出ない（権限）。

---

## よくある質問 / 注意
- **どれから？** まず **Path A**（画面確認）→ 準備でき次第 **Path B**（公開）。移行 **Path C** は任意のタイミング。
- **費用**: サーバーレス構成で **月 数百円規模**の想定（アクセス小規模時）。
- **独自ドメイン**: Phase 1 は CloudFront の無料ドメインで公開。独自ドメインは後から追加可能（ACMは us-east-1）。
- **管理画面（投稿・問い合わせ管理・ログイン）**: **Phase 2 実装済み** → 上の **Path D** で公開（`iyf-admin-web`）。管理者は MFA 必須。
- **サンプル文章**: 紹介/沿革/規約/入会費用は仮テキスト。実内容に差し替えてください（`iyf-public-web/src/pages/`）。

## つまずいたら
- `sam deploy` 認証エラー → `aws configure`（東京）/ SSOなら `aws sso login`
- `npm` が無い → Node.js 20 LTS を導入
- 問い合わせメールが届かない → SESの送信元検証・サンドボックス解除、SSMパラメータ設定を確認
