# ビジネスロジックモデル (Business Logic Model) — U3 backend-api

各モジュールの処理フローと状態遷移を技術非依存で示す。

---

## 状態遷移

### Post / Notice の公開状態（F5=A：予約公開なし）
```
[draft] --publish--> [published]
[published] --unpublish--> [draft]
[draft/published] --delete--> (削除)
```
- publish 時に publishedAt を確定（初回公開時刻）。再公開では既存 publishedAt を維持（運用簡素化）。
- 一般公開APIは status=published のみ返す。

### Inquiry の対応状況（F2=B）
```
[new] --> [in_progress] --> [done]
（任意方向に変更可。監査のため updatedBy/updatedAt を記録）
```

---

## モジュール別 処理フロー

### content モジュール

**listPosts（公開）**
```
入力: page, pageSize(=10, F6=A), archiveMonth?
1. status=published のみ対象
2. publishedAt 降順で pageSize 分取得（ページング）
3. PostSummary(title, authorDisplayName, publishedAt, 抜粋) に整形
出力: Page<PostSummary>
```

**getPost（公開）**: postId 指定。published のみ。非公開/存在せずは NotFound。

**createPost / updatePost（管理）**
```
入力: actor(認可済), PostInput(title, bodyRichText, status)
1. 入力検証（長さ・必須・型）+ 本文サニタイズ
2. authorId=actor.userId, authorDisplayName=actor.displayName をスナップショット
3. status=published なら publishedAt を設定（未設定時）
4. 保存 + 監査ログ（who/when/what）
出力: postId / void
```
- updatePost は editor が自分の記事のみ更新可、admin は全記事可（business-rules 参照）。

**Notice も content 内で同型**（listNotices/getNotice/create/update/delete/setStatus）。

### calendar モジュール
**listEvents（公開）**: fromDate..toDate の Event を startAt 昇順で取得。
**create/update/deleteEvent（管理）**: 入力検証（startAt<=endAt など）→保存→監査ログ。

### contact モジュール
**submitInquiry（公開）**
```
入力: InquiryInput(name,email,message), clientMeta
1. レート制限/スパム判定（IP・頻度・CAPTCHA連携）→ 超過は拒否
2. 入力検証（必須・長さ・email形式）+ サニタイズ
3. Inquiry 保存（status=new, receivedAt=now(JST)）
4. SES で通知メール送信（送信先=設定値/後から変更可）
   - メール送信失敗時も問い合わせ保存は成功扱い（記録優先, 失敗はログ/リトライ）
出力: inquiryId（ユーザーには汎用完了メッセージ）
```

**listInquiries / getInquiry / updateInquiryStatus（管理）**
```
- listInquiries: receivedAt 降順、status で絞り込み可、ページング(10)
- updateInquiryStatus: status を new/in_progress/done へ変更、updatedBy/updatedAt 記録
```

### auth モジュール
**authorizeRequest（全管理APIの前段）**
```
入力: token(JWT), requiredRole
1. 署名・失効・aud/iss をサーバー側検証（SECURITY-12）
2. User.status=active 確認（disabled は拒否）
3. role が requiredRole を満たすか判定（admin>editor）
出力: Principal（userId, role, displayName） / 401・403（fail-closed）
```

**inviteEditor（admin）**: email 検証→Cognito 招待作成（role=editor, status=active）→招待メール。重複は冪等/エラー。
**setUserStatus（admin）**: active/disabled 切替（自分自身の無効化は禁止）。
**listUsers（admin）**: User 一覧（role/status/displayName）。

### 移行連携（U4）
- BlogMigrationTool は content.createPost を source=migrated・publishedAt=元記事日で呼ぶ。重複は外部キー（元URL/元ID→postId マップ）で回避。

---

## データ入出力の要点
- **入力**: すべて common の検証層を通過（型・長さ・形式・サニタイズ）
- **出力**: 公開APIは公開データのみ。エラーは汎用メッセージ＋詳細はログ
- **監査**: 管理系の作成/更新/削除/状態変更は who/when/what を記録（SECURITY-13/14）
- **タイムゾーン**: 保存・比較は JST 基準（F4=A）
