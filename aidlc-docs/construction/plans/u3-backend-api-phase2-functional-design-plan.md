# U3 backend-api (Phase 2) — Functional Design Plan & Questions

**対象ユニット**: U3 backend-api（Phase 2 管理系 = auth モジュール + 各サービスの管理メソッド）
**対象ストーリー**: US-07(ブログ投稿) / US-09(お知らせ投稿) / US-11(カレンダー登録) / US-14(問い合わせ管理) / US-15(ログイン) / US-16(編集者招待) / US-18(セキュリティ)
**前提（Phase 1 で確定済み・再質問しない）**:
- ドメインエンティティ（Post/Notice/Event/Inquiry/User）は `construction/u3-backend-api/functional-design/domain-entities.md` で定義済み。role=admin/editor、status=draft/published、Inquiry status=new/in_progress/done、authorDisplayName スナップショット保持。
- 認証は Cognito（JWT）＋ API Gateway JWT オーソライザがトークン検証。U3 は「ロール/オーナー認可」を担当（`src/common/auth.py` に deny-by-default 土台あり）。
- 管理系変更は監査記録（誰が/いつ/何を, SECURITY-13/14）。リッチテキストはサニタイズ（SECURITY-05）。

---

## Part 1 — 設計プラン（チェックボックス）

- [x] 認可マトリクス（操作 × ロール admin/editor）の確定
- [x] Editor のオーナーシップ制約（自記事のみ編集/削除 = IDOR 防止, SECURITY-08）の確定
- [x] 招待フロー（inviteEditor）の状態遷移と Cognito 連携の確定
- [x] ユーザー無効化（setUserStatus）の挙動と既存投稿への影響の確定
- [x] draft/published 状態遷移ルール（公開/非公開化の可否・権限）の確定
- [x] 管理系 API 契約（一覧に draft を含めるか等）の確定
- [x] 監査ログ項目の確定
- [x] business-logic-model-admin.md / business-rules-admin.md / domain-entities-admin.md の生成

---

## Part 2 — 質問（各 [Answer]: に A/B/... で回答してください）

### Question 1 — Editor の投稿削除権限（US-07）
US-07 は「自記事編集は可、全体権限は Admin のみ」。**Editor による削除**の扱いは？

A) Editor は自分の記事/お知らせを「編集」も「削除」もできる（Admin は全件可）

B) Editor は自分の記事/お知らせを「編集」のみ可、「削除」は Admin のみ

C) Editor は編集も削除も不可（作成と自記事の下書き保存まで。公開・削除は Admin）

X) Other（[Answer]: の後に記述）

[Answer]:A

### Question 2 — Editor の公開（published 化）権限（US-07/09）
Editor は記事/お知らせを**自分で「公開」**できますか？

A) できる（作成者が自分で公開まで完結。Admin 承認は不要）

B) 下書き保存までは Editor 可、published への切替（公開）は Admin のみ

X) Other（[Answer]: の後に記述）

[Answer]:A

### Question 3 — Editor が扱えるコンテンツ種別
ストーリー上、ブログ(US-07)とお知らせ(US-09)は [P3 Admin][P4 Editor] 両方、カレンダー(US-11)と問い合わせ(US-14)は [P3 Admin] のみです。この境界で確定してよいですか？

A) 確定：Editor = ブログ+お知らせのみ / カレンダー・問い合わせ管理・ユーザー招待は Admin のみ

B) Editor もカレンダー登録(US-11)を可能にする

C) Editor も問い合わせ管理(US-14)を可能にする

X) Other（[Answer]: の後に記述）

[Answer]:B

### Question 4 — 編集者招待の方式（US-16）
inviteEditor の実装方式は？（Cognito 前提）

A) Cognito `AdminCreateUser`（管理者がメール＋表示名を入力→ Cognito が招待メール＋仮パスワード送付→初回ログインで本パスワード設定）。role は Cognito グループ(editor)で付与、U3 は User プロファイル(displayName/status)を DynamoDB に保存

B) 招待リンク方式（U3 が招待トークンを発行しメール送付→リンクから本人がサインアップ）

X) Other（[Answer]: の後に記述）

[Answer]:A

### Question 5 — 招待時の表示名(displayName)
Post.authorDisplayName の元になる displayName はいつ確定しますか？

A) 招待時に Admin が入力（招待フォームで email＋displayName＋role を指定）

B) 招待された本人が初回ログイン時に自分で設定

X) Other（[Answer]: の後に記述）

[Answer]:B

### Question 6 — ユーザー無効化(setUserStatus=disabled)の挙動
Editor を無効化した場合の扱いは？

A) Cognito 側で無効化（以後ログイン不可）＋ U3 の User.status=disabled。**既存の公開記事はそのまま表示**（authorDisplayName はスナップショットで保持）

B) 無効化時に本人の下書きも非公開/凍結する

X) Other（[Answer]: の後に記述）

[Answer]:A

### Question 7 — 管理系一覧に draft を含めるか（US-07/09/14）
管理画面の一覧 API（listPosts/listNotices の Admin 版）は下書きも返しますか？

A) 管理系一覧は draft+published の全件を返す（公開系 API は published のみ、で分離）

B) 管理系一覧も published のみ（下書きは別画面/別APIで取得）

X) Other（[Answer]: の後に記述）

[Answer]:A

### Question 8 — 監査ログの保存先
管理系ミューテーション（作成/更新/削除/公開/招待/状態変更）の監査記録の保存先は？

A) 構造化ログ（CloudWatch Logs）に出力（相関ID・actor・action・対象ID・時刻）。専用テーブルは作らない（低コスト優先, NFR-COST）

B) DynamoDB に監査専用テーブルを設けて永続化（検索性重視）

X) Other（[Answer]: の後に記述）

[Answer]:A

---

**回答が終わったら「done」等でお知らせください。** 回答を読み取り、矛盾チェック後に Functional Design 成果物（business-logic-model / business-rules / domain-entities 追補）を生成します。未回答・曖昧な回答があれば追加質問します。
