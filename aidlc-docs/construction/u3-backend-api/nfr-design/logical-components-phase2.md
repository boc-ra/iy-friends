# Logical Components（Phase 2 追補）— U3 backend-api

Phase 1 `logical-components.md` を継承。Phase 2 で **auth モジュールを本格化**し、管理系ハンドラ・Cognito 連携・追加 GSI を加える。物理リソース確定は Infrastructure Design（U3/U5）。

---

## 1. 追加・変更される論理コンポーネント

| モジュール | Phase 2 での役割 | 主なエンティティ | 主な依存 |
|---|---|---|---|
| **auth**（新規本格化） | 認可判定、招待、ユーザー管理、プロファイル完了、Cognito 連携 | UserProfile, Principal | Cognito(cognito-idp), DynamoDB(Users), common |
| **common**（拡張） | `auth.py` を require_role/require_owner に本実装化、`audit.py` を管理系で利用 | Principal | Cognito claims, CloudWatch |
| **content**（拡張） | 管理メソッド（create/update/delete/setStatus, list_admin） | Post, Notice | common, DynamoDB(GSI-status追加) |
| **calendar**（拡張） | 管理メソッド（create/update/delete, 共有編集） | Event | common, DynamoDB |
| **contact**（拡張） | 管理メソッド（list/get/updateStatus, Admin限定） | Inquiry | common, DynamoDB(GSI-status既存) |
| **handlers/admin.py**（新規） | 認証必須ルーティング入口。ガード→検証→service→監査 | — | AdminApiGateway |

## 2. auth モジュール内部構成
```
auth/
  models.py       # UserProfile, Principal, Role(enum admin/editor), InviteRequest, profileState
  repository.py   # UserProfileRepository: get/put/list(Scan≤10)/update_status/complete_profile
  cognito.py      # CognitoClient: admin_create_user / add_to_group / disable / enable  (副作用隔離・retry・stub可)
  service.py      # AuthService: invite_editor / complete_profile / list_users / set_user_status / ensure_profile / require_postable
```

## 3. 追加インフラ論理要素（Phase 2）

| 要素 | 用途 | 採否 | 備考 |
|---|---|---|---|
| **Cognito User Pool + Groups(admin/editor)** | 認証・MFA・招待・ロール source | 採用 | MFA=Admin必須TOTP、token 1h/1h/30d |
| **AdminApiGateway（or 既存APIに /admin ルート + JWTオーソライザ）** | 管理系入口・認可・スロットリング | 採用 | CORS=admin-webオリジン限定 |
| **DynamoDB `GSI-status`（Posts/Notices）** | 管理系一覧（draft含む） | 採用（新規） | PK=status, SK=updatedAt desc |
| **Cognito 管理操作向け IAM 権限** | AdminCreateUser 等 | 採用（最小権限） | 対象 User Pool 限定、ワイルドカード禁止（SECURITY-06） |
| DynamoDB `Users` GSI-email | email 逆引き | **不採用** | 一意性は Cognito が担保（変更可） |
| DynamoDB `Users` GSI-all-users | listUsers | **不採用** | ≤10件 Scan で充足（変更可） |
| WAF / 独自レート制限 | 濫用対策 | **不採用** | APIGW既定+Cognito組込で充足（N4=A） |
| 監査専用テーブル | 監査 | **不採用** | CloudWatch Logs（Q8=A） |

## 4. 管理系データフロー（Phase 2 詳細）

### 4.1 記事の作成→公開（Editor）
```
admin-web → AdminApiGateway(JWT authz, throttle) → Lambda(handlers/admin)
  1. require_authenticated → Principal(sub, role=editor)
  2. require_role(admin, editor)
  3. AuthService.ensure_profile → require_postable(profileState=complete?)  ← pending は 409
  4. validate(PostInput) + sanitize(bodyRichText)
  5. ContentService.create_post: authorId=sub, authorDisplayName=snapshot, status=draft/published
     - published なら BR-STATE-02 検証 + publishedAt=now(JST)
  6. Repo PutItem(Posts) [+ GSI-status 自動反映]
  7. common.audit('post.create'/'post.publish', target=postId)
```

### 4.2 編集者招待（Admin）
```
admin-web → AdminApiGateway → Lambda(handlers/admin)
  1. require_role(admin)
  2. validate/normalize email
  3. AuthService.invite_editor:
       - CognitoClient.admin_create_user(email, temp_pw, EMAIL 配信)  → sub
       - CognitoClient.add_to_group(sub, 'editor')
       - UserProfileRepo.put(stub: role=editor, status=active, profileState=pending, invitedBy=admin)
       - audit('user.invite', target=sub)
   （重複 email → Cognito 例外 → 409）
```

### 4.3 初回ログイン→プロファイル完了
```
Editor: Cognito でログイン(仮PW→新PW) → admin-web
admin-web → PUT /admin/me/profile {displayName}
  AuthService.complete_profile: validate(1..40) → UserProfileRepo.update(profileState=complete, displayName)
```

### 4.4 ユーザー無効化（Admin）
```
require_role(admin) → 自己/最後のadmin なら 409
  CognitoClient.admin_disable_user(userId)
  UserProfileRepo.update(status=disabled)
  audit('user.disable', target=userId)
（既存記事は authorDisplayName スナップショットで表示継続）
```

## 5. 非機能連携（Phase 2 追加）

| 連携 | パターン |
|---|---|
| handlers/admin ↔ common.auth | 全ルートで require_authenticated→require_role（必要に応じ require_owner）必須 |
| AuthService ↔ CognitoClient | 副作用隔離・bounded retry・冪等・fail-closed。テストはスタブ注入 |
| Service ↔ Repository | パラメータ化 Query/GetItem/PutItem。管理系一覧は GSI-status（Scanは listUsers の限定例外のみ） |
| 全 admin ハンドラ | 相関ID・構造化ログ・監査（PIIマスク） |

## 6. 後段への申し送り（Infrastructure Design / U5 infra）
- Cognito User Pool/App Client/Groups/MFA/トークン寿命/招待メールテンプレート、AdminApiGateway JWT オーソライザ・CORS・スロットリング値 → **U5 infra**
- `GSI-status`（Posts/Notices）の物理定義、Lambda 実行ロールへ cognito-idp Admin 操作の最小権限追加 → **U3/U5 Infrastructure Design**
- 初期 admin ブートストラップ手順 → U5 infra
