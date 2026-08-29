# iyf-admin-web（IYフレンズ 管理CMS / U2）

ミニバスケットボールチーム「IYフレンズ」の**管理画面**（認証SPA）。ブログ/お知らせ投稿、カレンダー登録、問い合わせ管理、編集者招待をスマホからも操作できる。Phase 2。

## 技術スタック
- React 18 + react-router-dom 6 + Vite + TypeScript（U1 public-web と同系・最小依存）
- 認証: **AWS Amplify v6**（Cognito SRP / TOTP MFA / トークン更新）
- 本文エディタ: **TipTap**（出力HTMLはバックエンドの allowlist に整合）
- スタイル: カスタムCSS（apple-design トークン）・スマホ最適化

## ディレクトリ
```
src/
  auth/       Amplify設定・AuthProvider（認証状態機械）・ProtectedRoute
  api/        types・client(authFetch)・dummy（擬似データ/ログイン）
  components/ Layout(TopBar/NavDrawer)・ui・Toast・ConfirmDialog・RichTextEditor(TipTap)
  pages/      Login/Profile/Dashboard/Post*/Notice*/Calendar*/Inquiry*/UserList/NotFound
  hooks/      useAsync
  lib/        format
  styles/     tokens.css / global.css / components.css
```

## セットアップ / 開発
```bash
npm install
cp .env.example .env      # 値を設定（未設定ならダミーモード）
npm run dev               # http://localhost:5174
npm run typecheck         # 型チェック
npm run build             # 本番ビルド（dist/）
```

### 環境変数（`.env`）
| 変数 | 用途 |
|---|---|
| `VITE_API_BASE_URL` | U3 AdminApi のベースURL。**未設定ならダミーモード** |
| `VITE_USER_POOL_ID` | U5 Cognito User Pool ID。**未設定ならダミー認証** |
| `VITE_USER_POOL_CLIENT_ID` | U5 Cognito App Client ID |
| `VITE_AWS_REGION` | 例: ap-northeast-1 |

### ダミーモード（U2-3=A）
`VITE_API_BASE_URL` / Cognito 未設定時は、バックエンド・Cognito 無しで画面確認できる。
ログイン画面でロール（admin/editor）を選び任意のメールで擬似ログイン。データはメモリ上のダミー。

## 認証フロー
`ログイン(SRP) → 新パスワード(初回) → MFA入力 or MFA登録 → 管理画面`。
**管理者は MFA(TOTP) 登録が必須**（未登録なら登録画面へ強制）。編集者は任意。
初回は `/profile` で表示名を設定（未設定だと記事の作成・公開が 409 になる）。

## ロールと権限（サーバー権威）
- **admin**: 全機能（問い合わせ管理・ユーザー招待/有効無効を含む）。
- **editor**: ブログ・お知らせ・カレンダー。自分の記事のみ編集/削除/公開（IDOR防止はサーバー側）。
- 画面のナビ/ルートガードは補助。最終的な認可は U3 API（403/409 を UI に反映）。

## デプロイ（U5 の S3/CloudFront）
```bash
npm run build
aws s3 sync dist/ s3://<U5のadmin用バケット>/ --delete
aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"
```
※ 管理配信は公開サイトと分離推奨（別 CloudFront/パス）。配信オリジンを U3 の `AllowedOrigins`(CORS) に登録する。
`index.html` は `noindex` 指定（検索避け）。SPA のため 403/404 を index.html へフォールバック。

## セキュリティ
- 認可はサーバー権威（U3 の JWT オーソライザ + ロール/オーナー）。本アプリは UX 補助。
- 本文は TipTap の許可ノードのみ。表示は U3 サニタイズ済みHTML。
- トークンは Amplify が保持・更新（access 1h / refresh 30d, U5）。
