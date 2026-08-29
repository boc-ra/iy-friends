# U2 admin-web — Functional Design Plan & Questions

**ユニット**: U2 admin-web（Phase 2 管理CMS フロントエンド・認証SPA）。新規リポジトリ `iyf-admin-web`。
**対象ストーリー**: US-07(ブログ投稿) / US-09(お知らせ投稿) / US-11(カレンダー登録) / US-14(問い合わせ管理) / US-15(ログイン・MFA) / US-16(編集者招待)。**スマホ最適化**（P3 はスマホ中心）。
**消費API**: U3 AdminApi（`/admin/*`、`Authorization: Bearer`）。認証は U5 Cognito（UserPoolId/ClientId）。
**規約（U1 踏襲）**: React 18 + react-router-dom 6 + Vite + TypeScript、最小依存、apple-design、カスタムCSS（tokens）、`VITE_API_BASE_URL` 未設定時はダミーモードで動作。

## 想定画面/ルート（確認対象）
```
/login                 ログイン（SRP, 新パスワード, MFA入力/登録）
/                      ダッシュボード（各種への導線・自分の下書き）
/posts                 ブログ一覧（draft含む・状態バッジ）
/posts/new /posts/:id  ブログ作成/編集（WYSIWYG・下書き/公開）
/notices …             お知らせ（同型）
/calendar              予定一覧・登録/編集（共有編集）
/inquiries             問い合わせ一覧・詳細・状態更新（admin のみ）
/users                 ユーザー一覧・招待・有効/無効（admin のみ）
/profile               自分の displayName 設定（初回必須）
```
ロールで表示制御（editor は inquiries/users 非表示）。admin は初回 MFA 登録を強制。

## 設計プラン（チェックボックス）
- [x] 認証ライブラリ確定 → U2-1=A **AWS Amplify v6**
- [x] WYSIWYG エディタ確定 → U2-2=A **TipTap**
- [x] ダミー/ローカルプレビュー方針確定 → U2-3=A **ダミーモードあり**
- [x] 画面/ルート・コンポーネント階層・props/state・フォーム検証・API結合点の確定
- [x] frontend-components.md 生成

---

## Question U2-1 — Cognito 認証ライブラリ
ログイン(SRP)・新パスワード・**TOTP MFA（登録/入力）**・トークン更新を扱います。

A) **AWS Amplify v6（`aws-amplify/auth`）**（推奨）。SRP・MFA・トークン更新を公式サポートで安定。やや大きめだが実装が堅実

B) **amazon-cognito-identity-js**（軽量）。SRP・MFA 対応、依存が小さい。メンテはやや停滞

C) **@aws-sdk/client-cognito-identity-provider 直叩き**（最小依存だが SRP/MFA を自前実装＝手間大）

X) Other

[Answer]:A

## Question U2-2 — WYSIWYG エディタ（ブログ/お知らせ本文）
バックエンドは allowlist サニタイズ（p/strong/em/ul/ol/li/a/h2/h3/blockquote/code/hr 等）。それに沿う HTML を出力します。

A) **TipTap**（`@tiptap/react`）。モダン・拡張容易・HTML出力を allowlist に制限しやすい。モバイル操作も良好（推奨）

B) **react-simple-wysiwyg**（超軽量）。最小限のツールバー、依存小。細かい制御は限定的

C) **Markdown テキストエリア**（自前・エディタ無し）。最軽量だが編集体験は素朴（保存時に Markdown→許可HTML変換が必要）

X) Other

[Answer]:A

## Question U2-3 — ローカルプレビュー（ダミーモード）
U1 同様、バックエンド/Cognito 無しでも画面確認できるダミーモードを用意しますか？

A) 用意する（`VITE_API_BASE_URL` 未設定時はダミーデータ＋擬似ログインで画面確認可）（推奨）

B) 不要（実 API/Cognito 前提のみ）

X) Other

[Answer]:A

---

**回答後「done」等でお知らせください。** 空欄なら推奨（A/A/A）を適用して進めます。回答を反映し frontend-components.md を生成します。
