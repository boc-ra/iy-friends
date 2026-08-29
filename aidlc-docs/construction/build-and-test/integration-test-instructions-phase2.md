# Integration Test Instructions（Phase 2 管理CMS）

## 目的
U5(Cognito) ↔ U3(AdminApi) ↔ U2(admin-web) の連携と、管理業務フローの疎通を確認する。

## 前提環境
```
1. U5 infra デプロイ（Cognito UserPool + Export）
2. U3 backend-api デプロイ（AdminFunction/JWT authorizer、U5 Export を Import）
   └ backfill_status 実行（既存 Posts/Notices の GSI-status 掲載）
3. 初期 admin ブートストラップ（iyf-infra/README の手順）
4. U2 admin-web: .env に VITE_API_BASE_URL / VITE_USER_POOL_ID / VITE_USER_POOL_CLIENT_ID を設定して起動
```

## シナリオ

### S1: 認証・認可（U5→U3→U2）
- admin でログイン → **MFA(TOTP) 登録が要求される**（未登録時）→ 登録後に管理画面へ。
- access token を付けて `GET /admin/posts` が 200。トークン無しは 401。
- editor で `GET /admin/inquiries` → **403**（Admin 専用）。
- **期待**: JWT オーソライザ + ロール認可が機能。

### S2: 投稿ライフサイクル（U2→U3）
- editor が新規記事を作成（下書き）→ 一覧に draft バッジ表示 → 公開 → 公開サイト(U1)の `/posts` に反映。
- 公開を取り下げ → U1 一覧から消える。
- 他人の記事を編集 → **403**（IDOR 防止）。自分の記事は編集/削除可。
- **期待**: 状態遷移・オーナー制がサーバー権威で機能。

### S3: プロフィール未完了ガード
- 招待直後（displayName 未設定）で記事作成 → **409** → admin-web が `/profile` へ誘導 → displayName 設定後は作成可。

### S4: 編集者招待（U3→Cognito）
- admin が `POST /admin/users/invite` → Cognito 招待メール送付 → 被招待者が初回ログイン → displayName 設定 → editor として投稿可。
- 重複 email 招待 → **409**。

### S5: 問い合わせ管理（U1→U3→U2）
- 公開サイト(U1)から問い合わせ送信 → admin-web の `/inquiries` に「未対応」で表示 → 状態を「対応済」に更新 → 反映。

### S6: カレンダー共有編集
- editor A が作成した予定を editor B が編集/削除できる（オーナー制なし）。

## 実行のヒント
- ダミーモード（`VITE_API_BASE_URL` 未設定）では S1–S6 の**UI挙動**を擬似確認可（実認可はサーバー未接続のため簡略）。
- 実疎通は上記デプロイ後に手動 or 将来の e2e（Playwright 等）で自動化。

## クリーンアップ
- テストで作成した Cognito ユーザー / DynamoDB アイテムを削除（`admin-delete-user`、テーブルの当該アイテム削除）。
