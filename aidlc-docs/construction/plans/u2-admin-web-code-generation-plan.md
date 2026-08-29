# U2 admin-web — Code Generation Plan（Part 1: Planning）

**ユニット**: U2 admin-web（管理CMS SPA）。**Greenfield 新規リポジトリ** `iyf-admin-web/`（ワークスペース直下）。
**規約**: React 18 + react-router-dom 6 + Vite + TypeScript（U1 踏襲）。認証=AWS Amplify v6、本文=TipTap、ダミーモードあり。apple-design・スマホ最適化。
**対象ストーリー**: US-07/09/11/14/15/16。設計: `construction/u2-admin-web/functional-design/frontend-components.md`。
**API 契約**: `construction/u3-backend-api/code/api-documentation-admin.md`。認証: U5 Cognito。

## ステップ（各完了で [x]）

### プロジェクト基盤
- [x] **Step 1**: `package.json`（react/react-dom/react-router-dom/aws-amplify/@tiptap/react/@tiptap/starter-kit/@tiptap/extension-link + vite/typescript/@types）、`vite.config.ts`、`tsconfig.json`、`index.html`、`.env.example`（VITE_API_BASE_URL/VITE_USER_POOL_ID/VITE_USER_POOL_CLIENT_ID/VITE_AWS_REGION）、`.gitignore`
- [x] **Step 2**: `src/main.tsx`（AuthProvider+BrowserRouter）、`src/App.tsx`（ルート定義・ProtectedLayout/ロールガード）、`src/vite-env.d.ts`
- [x] **Step 3**: `src/styles/`（`tokens.css`/`global.css`/`components.css` を U1 から取り込み・管理UI用に調整）、`src/lib/format.ts`（日付/状態表示）

### 認証（Amplify v6）
- [x] **Step 4**: `src/auth/amplifyConfig.ts`（env から設定・ダミー時スタブ）、`src/auth/AuthProvider.tsx`（Context: user/role/mfa/profile 状態＋ signIn/confirmNewPassword/confirmMfa/setupTotp/completeSignOut）、`src/auth/useAuth.ts`、`src/auth/ProtectedRoute.tsx`（未認証→/login、ロール/プロフィール ガード）

### API クライアント
- [x] **Step 5**: `src/api/types.ts`（Post/Notice/Event/Inquiry/UserSummary/status enum・入力型）、`src/api/client.ts`（`authFetch` = access token 付与、`ApiError`、posts/notices/events/inquiries/users/profile 関数、`USING_DUMMY` 分岐）、`src/api/dummy.ts`（ダミーデータ＋擬似ログイン・role切替）

### 共通コンポーネント
- [x] **Step 6**: `src/components/` 基本UI: `Layout.tsx`(ProtectedLayout+TopBar+NavDrawer)、`Button/TextField/Select/Modal/Toast/Loading/States(Error/Empty)/StatusBadge/ConfirmDialog`
- [x] **Step 7**: `src/components/RichTextEditor.tsx`（TipTap・allowlist準拠ツールバー: 太字/斜体/下線/取消/H2/H3/箇条書き/番号/リンク/引用/コード/hr、HTML入出力）

### ページ
- [x] **Step 8**: `src/pages/Login.tsx`（SRP→新PW→MFA入力→admin TOTP登録強制）、`Profile.tsx`（displayName 初回設定）
- [x] **Step 9**: `src/pages/Dashboard.tsx`（導線＋自分の下書き）
- [x] **Step 10**: `src/pages/PostList.tsx`・`PostEdit.tsx`（TipTap・下書き/公開/削除・オーナー制はサーバー権威）
- [x] **Step 11**: `src/pages/NoticeList.tsx`・`NoticeEdit.tsx`（ブログ同型）
- [x] **Step 12**: `src/pages/CalendarAdmin.tsx`・`EventEdit.tsx`（共有編集）
- [x] **Step 13**: `src/pages/InquiryList.tsx`・`InquiryDetail.tsx`（状態更新, admin）、`src/pages/UserList.tsx`（招待/有効無効, admin）
- [x] **Step 14**: `src/pages/NotFound.tsx`

### 仕上げ
- [x] **Step 15**: `README.md`（セットアップ・env・ダミーモード・ビルド/デプロイ[U5 S3/CloudFront]・認証注意）、型チェック（`tsc -b --noEmit`）で自己検証
- [x] **Step 16**: ドキュメント `aidlc-docs/construction/u2-admin-web/code/code-generation-summary.md`

## ストーリー・トレーサビリティ
US-15/16→Step4,8,13 / US-07→10 / US-09→11 / US-11→12 / US-14→13。

## 依存・前提
- U3 AdminApi 契約・U5 Cognito Export（UserPoolId/ClientId）。ローカルはダミーモードで完結。
- **検証**: `npm install` は本環境で行わず、`tsc` 型チェックは可能なら実施。ビルド/デプロイ実行は Build & Test（Phase 2）。TipTap/Amplify は実 npm 環境で解決。
- data-testid を主要操作要素に付与（code-generation.md）。

## スコープ・規模
新規リポジトリ 1式（設定6 + auth4 + api3 + components ~12 + pages ~14 + styles3 + docs）。合計 **16 ステップ**。

---
**この計画で Part 2（生成）を実行してよいか承認してください。**
