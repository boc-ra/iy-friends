# Frontend Components — U2 admin-web（管理CMS / Phase 2）

技術: React 18 + react-router-dom 6 + Vite + TypeScript（U1 踏襲・最小依存）。認証=AWS Amplify v6（U2-1=A）、本文エディタ=TipTap（U2-2=A）、ダミーモードあり（U2-3=A）。apple-design・**スマホ最適化**。
消費: U3 AdminApi（`/admin/*`, `Authorization: Bearer <access>`）。認証: U5 Cognito（`VITE_USER_POOL_ID`/`VITE_USER_POOL_CLIENT_ID`）。

---

## 1. ルート / 画面構成
| ルート | 画面 | ロール | 主API |
|---|---|---|---|
| `/login` | ログイン（SRP→新PW→MFA入力/登録） | 全 | Amplify Auth |
| `/` | ダッシュボード（導線＋自分の下書き） | 全 | `GET /admin/posts` |
| `/posts` | ブログ一覧（draft含む・状態バッジ） | admin/editor | `GET /admin/posts` |
| `/posts/new` `/posts/:id` | ブログ作成/編集（TipTap・下書き/公開/削除） | admin(全)/editor(自) | `POST/PUT/DELETE /admin/posts…`, `…/status` |
| `/notices` `/notices/new` `/notices/:id` | お知らせ（ブログ同型） | admin/editor | `/admin/notices…` |
| `/calendar` | 予定一覧・登録/編集/削除（共有編集） | admin/editor | `/admin/events…` |
| `/inquiries` | 問い合わせ一覧・詳細・状態更新 | **admin のみ** | `/admin/inquiries…` |
| `/users` | ユーザー一覧・招待・有効/無効 | **admin のみ** | `/admin/users…` |
| `/profile` | 自分の displayName 設定（初回必須） | 全 | `PUT /admin/me/profile` |
| `*` | NotFound | — | — |

- ロール制御: editor は `/inquiries` `/users` を**ナビ非表示＋ルートガードで拒否**。
- **admin 初回 MFA 強制**: admin グループかつ MFA 未登録 → `/login` の MFA 登録ステップへ強制（管理画面に入れない, U5 infra §3）。
- **profile 未完了**（displayName pending）→ `/profile` へ誘導（投稿系は完了まで不可、API も 409 を返す）。

## 2. コンポーネント階層
```
main.tsx → <AuthProvider><BrowserRouter><App/></...>
App (Routes)
├─ <ProtectedLayout>          認証必須の枠（未認証→/login）
│   ├─ <TopBar/>              タイトル・ユーザー名・ログアウト（モバイル: ハンバーガー）
│   ├─ <NavDrawer/>           ロール別メニュー（editor は inquiries/users 非表示）
│   └─ <Outlet/>              各ページ
│       ├─ Dashboard
│       ├─ PostList / PostEdit(<RichTextEditor/>,<StatusToggle/>)
│       ├─ NoticeList / NoticeEdit
│       ├─ CalendarAdmin / EventEdit
│       ├─ InquiryList / InquiryDetail(<StatusSelect/>)   [admin]
│       ├─ UserList / InviteForm(<Modal/>)                [admin]
│       └─ Profile
└─ <LoginPage> (公開ルート, 認証フロー)
```
共通: `<PageHeader/>`, `<Button/>`, `<TextField/>`, `<Select/>`, `<Modal/>`, `<Toast/>`, `<Loading/>`, `<ErrorState/>`, `<EmptyState/>`, `<StatusBadge/>`, `<ConfirmDialog/>`（削除確認）。

## 3. 認証（Amplify v6）
- `src/auth/`: `amplifyConfig.ts`（UserPoolId/ClientId, ダミー時はスタブ）、`AuthProvider.tsx`（Context: `user`, `role`, `mfaState`, `signIn/confirmNewPassword/confirmMfa/setupTotp/signOut`）、`useAuth()`。
- トークン: Amplify が保持・更新（access 1h / refresh 30d, U5）。API 呼び出し前に `fetchAuthSession()` で access token 取得。
- 認証フロー状態機械:
  ```
  SIGNED_OUT → (signIn) → NEW_PASSWORD_REQUIRED? → (confirm) →
    MFA(SOFTWARE_TOKEN)? → (confirmMfa) →
    [admin かつ MFA未登録] → TOTP_SETUP(associate→verify→setPreference) →
    PROFILE_PENDING? → /profile → SIGNED_IN
  ```

## 4. API クライアント（`src/api/`）
- `client.ts`: `authFetch(path, init)` = `fetchAuthSession()` の access token を `Authorization` に付与→ `fetch`。`USING_DUMMY`（`VITE_API_BASE_URL` 未設定）ならダミー。
- エラー: `ApiError{status}`。401→再ログイン誘導 / 403→権限エラー表示 / 409→「プロフィール未完了」等の業務メッセージ / 422→入力エラー。
- 関数: posts/notices（list/get/create/update/remove/setStatus）, events（list/create/update/remove）, inquiries（list/get/setStatus）, users（list/invite/setStatus）, profile（complete）。
- `types.ts`: U3 のレスポンス型（Post/Notice/Event/Inquiry/UserSummary、status enum）。U1 の types を拡張。
- `dummy.ts`: ダミーデータ＋擬似ログイン（role 切替可）。

## 5. 主要コンポーネント props/state（抜粋）
- `RichTextEditor{ value:string(html); onChange(html); }` — TipTap。許可マーク: bold/italic/underline/strike, H2/H3, bullet/ordered list, link, blockquote, code, hr。出力はバックエンド allowlist に一致（超過タグは不使用）。
- `PostEdit` state: `{title, body(html), category?, status, loading, error, dirty}`。保存=create/update、公開切替=setStatus。削除=ConfirmDialog→remove。
- `InviteForm` state: `{email, submitting, error}` → `POST /admin/users/invite`。成功で一覧更新＋Toast。
- `StatusSelect`（問い合わせ）: new/in_progress/done → `PUT …/status`。
- `Profile` state: `{displayName}` → `PUT /admin/me/profile`。完了で投稿系解禁。

## 6. フォーム検証（クライアント側・SECURITY-05 の一次防御）
- title 1..200 / body 非空（公開時）/ email 形式 / displayName 1..40 / event_date 必須。
- サーバー検証が最終権威（422/409 を UI に反映）。XSS: 本文は TipTap の許可ノードのみ、表示は U3 サニタイズ済み HTML を `dangerouslySetInnerHTML`（許可タグのみ）。

## 7. モバイル最適化（P3 スマホ中心, NFR-UX）
- 1カラム・大きめタップ領域（44px+）・ドロワーナビ・下部固定の主要アクション（保存/公開）。
- apple-design: 余白・タイポ・控えめな動き・`prefers-reduced-motion` 尊重。tokens.css を U1 と共有方針（コピー）。

## 8. 自動化フレンドリ（code-generation.md）
- 主要操作要素に `data-testid`（例: `login-submit`, `post-editor-save`, `post-status-toggle`, `invite-email-input`, `user-invite-submit`, `inquiry-status-select`）。安定命名 `{screen}-{role}`。

## 9. トレーサビリティ
- ストーリー: US-07/09/11/14/15/16。US-18（認可はサーバー権威＋クライアント補助）。
- 依存: U3 AdminApi 契約（`api-documentation-admin.md`）、U5 Cognito（UserPoolId/ClientId）。
- 反映回答: U2-1=A / U2-2=A / U2-3=A。
