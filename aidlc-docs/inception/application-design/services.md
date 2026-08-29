# サービス定義 (Services) — IYフレンズ公式サイト

サービス層の定義と、リクエストのオーケストレーション（調整）パターンを示す。
バックエンドはサーバーレス（API Gateway + Lambda + Python）。認可境界で Public/Admin を分離。

---

## サービス一覧

| サービス | 責務 | 認可 | 主データ | 外部連携 |
|---|---|---|---|---|
| ContentService | ブログ/お知らせ/静的ページの管理・公開 | Public(読取)/Admin(更新) | Posts, Notices | — |
| CalendarService | 活動予定の管理・公開 | Public(読取)/Admin(更新) | Events | — |
| ContactService | 問い合わせ受付・保存・通知・履歴 | Public(送信)/Admin(管理) | Inquiries | SES(メール) |
| AuthService | 認証/認可・招待・アカウント運用 | Admin | Users(Cognito) | Cognito |

---

## オーケストレーション・パターン

### パターン1: 公開コンテンツ取得（読み取り・認証不要）
```
PublicWebApp(SSG/CSR)
   -> PublicApiGateway
      -> Lambda(ContentService/CalendarService)
         -> DynamoDB(公開済みのみ)  -> レスポンス(キャッシュ可)
```
- SSG のビルド時取得＋公開後の差分はクライアント側取得（CSR）で補完
- CloudFront でキャッシュし低コスト・高速化（NFR-COST/PERF）

### パターン2: お問い合わせ送信（公開・書き込み）
```
PublicWebApp(フォーム)
   -> PublicApiGateway(レート制限)
      -> Lambda(ContactService)
         1) 入力検証・スパム対策(SECURITY-05/11)
         2) DynamoDB(Inquiries) へ保存
         3) SES で通知メール送信(送信先は設定値)
      -> 送信完了レスポンス(汎用)
```

### パターン3: 管理操作（投稿・認証必須）
```
AdminWebApp(ログイン済/JWT)
   -> AdminApiGateway
      -> Lambda(AuthService.authorizeRequest でトークン検証+ロール認可)  ← 全AdminAPI共通の前段
         -> 該当サービス(ContentService/CalendarService/ContactService)
            -> DynamoDB 更新 + 監査ログ(SECURITY-13/14)
      -> 結果レスポンス(fail-closed)
```

### パターン4: 編集者招待（管理者のみ）
```
AdminWebApp(Adminロール)
   -> AdminApiGateway
      -> Lambda(AuthService.inviteEditor)  [Adminロール検証]
         -> Cognito(招待/ユーザー作成)
         -> 招待メール(Cognito/SES)
      -> 結果レスポンス
```

### パターン5: ブログ移行（バッチ・一度きり/再実行可）
```
BlogMigrationTool(バッチ)
   -> scrapeSource(現行サイト)
   -> normalize(記事整形/画像除外)
   -> importPosts -> ContentService -> DynamoDB(Posts)
   -> ImportReport(件数/重複/失敗)
```

---

## サービス設計方針
- **認可の一元化**: AdminApi は AuthService.authorizeRequest を共通前段に置き、各サービスは業務に専念（Defense in depth, SECURITY-08/11）
- **公開/管理の分離**: 別 API Gateway・別フロントアプリ（Q-A2=A）でセキュリティ境界を明確化
- **ステートレス**: Lambda はステートレス、状態は DynamoDB / Cognito に保持
- **最小権限**: 各 Lambda の IAM ロールは必要な DynamoDB/SES/Cognito 操作のみ（SECURITY-06）
- **可観測性**: 全サービスで構造化ログ＋主要メトリクス/アラート（SECURITY-03/14）
- **コスト最適化**: 従量課金・キャッシュ活用・不要な常時稼働リソースを持たない（NFR-COST-01）
