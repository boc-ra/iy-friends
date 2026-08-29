# ドメインエンティティ 追補 (Domain Entities — Admin) — U3 backend-api / Phase 2

Phase 1 の `domain-entities.md` を拡張。Phase 2（管理系）で**新規に増える概念**と、**既存エンティティのライフサイクル精緻化**のみを記す。新規の永続エンティティは実質 `UserProfile`（既存 User の実体化）と概念上の `AuditEvent`（ログ）のみ。

---

## Entity（精緻化）: UserProfile（= 既存 User の U3 側プロファイル）

認証情報は Cognito が保持。U3 は下記プロファイルを DynamoDB に保持する（Phase 1 の User 定義を実装レベルに精緻化）。

| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| userId | string (Cognito sub) | ● | 一意ID（PK） |
| email | string(email, 正規化) | ● | ログインID／招待先。小文字・trim 正規化 |
| displayName | string(1..40) \| null | 初回ログイン後● | 表示名。**招待直後は null(pending)**、本人が初回ログインで設定（Q5=B, BR-USER-02） |
| role | enum(admin, editor) | ● | 役割。Cognito グループを正とし、ここはミラー（BR-AUTH-03） |
| status | enum(active, disabled) | ● | 有効/無効。無効化で Cognito も AdminDisableUser（Q6=A, BR-USER-04） |
| profileState | enum(pending, complete) | ● | displayName 設定前=pending / 後=complete。pending は投稿不可 |
| invitedBy | string (userId) | | 招待した管理者。ブートストラップ admin は null |
| createdAt | datetime(JST) | ● | 作成（招待）日時 |
| updatedAt | datetime(JST) | ● | 更新日時 |

### UserProfile ライフサイクル（状態機械）
```
[invite (Admin)]                 Cognito: AdminCreateUser + editor group
      │  create stub
      ▼
(status=active, profileState=pending)      ← 招待メール+仮PW送付済
      │  初回ログイン(仮PW→新PW) → completeProfile(displayName)
      ▼
(status=active, profileState=complete)      ← 投稿・公開が可能
      │  setUserStatus(disabled) [Admin]  → Cognito AdminDisableUser
      ▼
(status=disabled)  ── setUserStatus(active) ──►（複帰: displayName 保持）
```
- **不変条件**: 自分自身・最後の有効 admin は disabled にできない（BR-USER-04）。
- **投稿可否**: `profileState=complete` かつ `status=active` のときのみ create/publish 可（BR-USER-02）。

---

## Concept: Principal（認可コンテキスト・非永続）

リクエスト単位の認可情報（JWT claim 由来、永続化しない）。
```
Principal{ sub: string, role: 'admin'|'editor', groups: list[string] }
```
- `require_role` / `require_owner` の入力（`common/auth.py`）。

---

## Concept: AuditEvent（監査ログ・CloudWatch, 非DynamoDB）（Q8=A）

永続テーブルは作らず構造化ログとして出力（BR-AUDIT）。論理スキーマ:
```
AuditEvent{
  correlationId: string,
  timestamp: datetime(JST),
  actorId: string(sub),
  actorRole: 'admin'|'editor',
  action: string,              # 例: post.create / post.publish / user.invite / inquiry.status
  targetType: string,          # post|notice|event|inquiry|user
  targetId: string,
  result: 'success'|'deny'|'error',
  changedFields?: list[string] # キー名のみ。値・PII・本文は含めない (SECURITY-03)
}
```

---

## 既存エンティティへの Phase 2 影響（差分）

| エンティティ | Phase 2 での扱い |
|---|---|
| Post | 属性変更なし。admin 経由の create/update/delete/setStatus 対象に。`authorId`=作成者 sub, `authorDisplayName`=スナップショット確定。draft は管理系一覧のみ可視 |
| Notice | Post と同型（authorId ありオーナー制） |
| Event | 属性変更なし。**authorId を持たない**ため共有編集（BR-OWN-03）。作成/更新者は AuditEvent で追跡 |
| Inquiry | 属性変更なし。`status`（new/in_progress/done）更新と `updatedBy`/`updatedAt` を管理系で使用 |
| User | 本書 `UserProfile` として実体化（profileState 追加） |

---

## キー設計・整合性の注記（NFR/Infra で確定）
- UserProfile の PK/GSI（email 逆引き・重複検査用 GSI 等）、Post/Notice の draft を含む管理系クエリ用アクセスパターン（status + 時刻ソート、authorId 絞り込み）は **NFR Design / Infrastructure Design（U3/U5）で確定**する。
- 本 Functional Design はキー設計に依存しない業務ルール・状態遷移までを確定範囲とする。
