# Code Generation Summary — U2 admin-web（管理CMS / Phase 2）

Greenfield 新規リポジトリ `iyf-admin-web/`（Vite + React 18 + TypeScript）。**型チェック通過・本番ビルド成功**（708 modules, gzip ≈198KB）。

## 生成物（主なファイル・34 src ファイル）
- **基盤**: `package.json`（+aws-amplify 6 / @tiptap 2）, `vite.config.ts`, `tsconfig.json`, `index.html`(noindex), `.env.example`, `.gitignore`, `src/main.tsx`, `src/App.tsx`
- **認証(`src/auth/`)**: `amplifyConfig.ts`（env 設定・ダミー判定）, `session.ts`（access token 取得）, `AuthProvider.tsx`（認証状態機械: signedOut→newPassword→mfa/mfaSetup→signedIn、**admin 未登録MFAの強制TOTP登録**）, `useAuth.ts`, `ProtectedRoute.tsx`（RequireAuth/RequireRole）
- **API(`src/api/`)**: `types.ts`, `client.ts`（`authFetch` = Bearer 付与、409→/profile 誘導等のエラーメッセージ、`USING_DUMMY` 分岐）, `dummy.ts`（擬似データ/操作/ログイン）
- **コンポーネント(`src/components/`)**: `Layout.tsx`(TopBar+ロール別NavDrawer), `ui.tsx`(Button/Field/TextField/TextArea/Select/StatusBadge/Loading/Error/Empty), `Toast.tsx`, `ConfirmDialog.tsx`, `RichTextEditor.tsx`(**TipTap・allowlist準拠ツールバー**)
- **ページ(`src/pages/`)**: Login, Profile, Dashboard, PostList/PostEdit, NoticeList/NoticeEdit, CalendarAdmin/EventEdit, InquiryList/InquiryDetail, UserList, NotFound
- **その他**: `hooks/useAsync.ts`, `lib/format.ts`(流用), `styles/`(tokens/global 流用 + admin用 components.css), `README.md`

## 実装対応（設計 → 実装）
| 決定 | 実装 |
|---|---|
| U2-1=A Amplify v6 | `AuthProvider` が SRP/新PW/MFA入力/MFA登録/更新を処理。`fetchAuthSession` の access token を `authFetch` が付与 |
| admin MFA 強制（U5-1=A の補完） | サインイン後 `fetchMFAPreference`、admin×未登録なら `setUpTOTP`→`verifyTOTPSetup`→`updateMFAPreference` を強制 |
| U2-2=A TipTap | StarterKit(+Underline/Link)。ツールバーは B/I/U/S/H2/H3/UL/OL/引用/コード/リンク/hr = バックエンド allowlist に一致 |
| U2-3=A ダミーモード | `VITE_API_BASE_URL`/Cognito 未設定でダミーデータ＋擬似ログイン（role切替可） |
| ロール制御 | NavDrawer 非表示＋`RequireRole` ガード（inquiries/users=admin）。最終認可はサーバー（403/409 を UI 反映） |
| オーナー制/公開ルール | サーバー権威。UI は 403/409/422 をメッセージ化。プロフィール未完了(409)→ `/profile` 誘導 |
| 状態遷移 | PostEdit/NoticeEdit で下書き保存/公開/公開取り下げ/削除（ConfirmDialog） |
| スマホ最適化 | 1カラム・44px タップ領域・ドロワー・sticky アクション。apple-design トークン・reduced-motion 尊重 |
| 自動化 | 主要操作に `data-testid`（login-submit, post-publish, invite-submit, inquiry-status-select 等） |

## 自己検証
- `npx tsc -b --noEmit` → **エラーなし**
- `npm run build` → **成功**（dist 生成、gzip ≈198KB）。バンドルは Amplify+TipTap で 500KB 超の警告あり（内部管理ツールのため許容。将来 code-split 可）

## 既知事項・申し送り（Build & Test / デプロイ）
- 実 API/Cognito 連携の疎通は `.env` 設定後に確認（本 Code Gen はダミー＋型/ビルドで検証）。
- イベント個別 GET は U3 未提供のため、EventEdit は一覧から対象を特定（小規模で許容。将来 `GET /admin/events/{id}` 追加で最適化可）。
- displayName 未完了の判定は GET/me 不在のため**アクション時の 409 起点**（設計どおり）。
- デプロイは U5 の管理用 S3/CloudFront（公開と分離推奨）。配信オリジンを U3 `AllowedOrigins` に登録。

## トレーサビリティ
- ストーリー: US-07/09/11/14/15/16。設計: `../functional-design/frontend-components.md`。
- 依存: U3 AdminApi（`../../u3-backend-api/code/api-documentation-admin.md`）、U5 Cognito Export。
- 反映回答: U2-1=A / U2-2=A / U2-3=A。
