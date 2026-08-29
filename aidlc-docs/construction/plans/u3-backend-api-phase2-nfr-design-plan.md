# U3 backend-api (Phase 2) — NFR Design Plan

**対象**: U3 Phase 2（auth + 管理API）の NFR を設計パターン・論理コンポーネントへ落とし込む。
**前提**: Phase 1 の `nfr-design/`（マルチテーブル・On-Demand・deny-by-default・同期処理・キュー/DAX不採用）を継承。NFR Requirements Phase2（MFA=Admin必須TOTP・token 1h/1h/30d・APIGWスロットリング＋Cognito）確定済み。

## 設計判断（ユーザー質問なしで確定 — 規模と既存決定から一意に導出。**変更可**）
本ステージは新規のユーザー質問を発行しない。理由: 管理系のアクセスパターンは Phase 1 のテーブル設計（Posts/Notices/Events/Inquiries/Users）と規模（記事~339件、管理ユーザー≤10名）から最適解が一意に決まるため。以下を採用し、完了メッセージで明示する。

- [x] **認可パターン**: API Gateway JWT オーソライザ（トークン検証）＋ アプリ層 `common/auth.py`（require_role / require_owner）。deny-by-default。
- [x] **管理系一覧アクセスパターン（Posts/Notices）**: 既存 `GSI-published` に加え **`GSI-status`（PK=status, SK=updatedAt降順）** を追加。admin 一覧は draft/published を Query。Editor の「自 draft」は draft 結果を Lambda 内で authorId フィルタ（draft 件数は小、追加 GSI 不要）。将来 draft 増大時は `GSI-author` を追加可。
- [x] **UserProfile / email 一意性**: email の一意性は **Cognito を正**とする（AdminCreateUser が重複を拒否／必要時 ListUsers filter）。`Users` テーブルは PK=userId(sub) のまま、GSI-email は当面不要。
- [x] **listUsers**: `Users` は極小（≤10）につき **Scan 許容**（管理者のみ・低頻度）。Phase 1「Scan回避」原則の限定例外として明記。将来増大時は `GSI-all-users`（定数PK+createdAt）へ。
- [x] **Cognito 連携の隔離**: `auth/cognito.py` に副作用を集約（テストでスタブ化, 冪等・bounded retry, fail-closed）。
- [x] **監査**: `common/audit.py` を管理系イベントで利用（CloudWatch 構造化ログ、PIIマスク）。
- [x] **エラーマッピング**: 401/403/404/409/422/429 → 汎用メッセージ（fail-closed, SECURITY-15）。
- [x] nfr-design-patterns-phase2.md / logical-components-phase2.md の生成

> 上記いずれかを変えたい場合は「Request Changes」で指定してください（特に: Editor自draftを GSI-author 化するか、email 逆引き GSI を持つか、listUsers を GSI 化するか）。
