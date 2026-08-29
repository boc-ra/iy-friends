# Infrastructure Design（Phase 2 追補）— U3 backend-api

Phase 1 `infrastructure-design.md` を継承。Phase 2（管理API）の SAM 追加リソースを定義。
反映: functional/nfr-design Phase2、現行 `iyf-backend-api/template.yaml`、`iyf-infra/template.yaml`（Cognito 済）。

---

## 1. 論理 → 物理 対応表（Phase 2 追加分）

| 論理コンポーネント | AWS リソース | 主要設定 |
|---|---|---|
| 管理系実行 | **AWS Lambda `AdminFunction`**（Python 3.13, arm64） | `src.handlers.admin.handler`。既存 Globals（256MB/10s）踏襲。内部ルーティングで管理ルートを処理 |
| 管理系認可 | **HTTP API JWT オーソライザ**（既存 `HttpApi` に追加） | issuer=Cognito UserPool、audience=UserPoolClientId。管理ルートにのみ適用 |
| 認証基盤（参照） | **Cognito UserPool（U5 所有）** | `Fn::ImportValue: iyf-${Stage}-UserPoolId` / `-UserPoolClientId` を参照 |
| 管理系一覧索引 | **DynamoDB GSI 追加** | Posts/Notices=`GSI-status`（status, updated_at_epoch）、Inquiries=`GSI-status`（status, created_at_epoch） |
| ユーザー管理 | **cognito-idp Admin API** | AdminFunction ロールに最小権限付与（UserPool ARN 限定） |
| 監査/ログ | **CloudWatch Logs**（AdminFunction ロググループ, 90日） | 構造化ログ・監査イベント |

## 2. API 構成（単一 HttpApi + ルート単位認可）

- 既存 `HttpApi` を維持。**別 API Gateway を新設しない**（低コスト）。
- 管理ルートに **`Authorizer: CognitoJwt`** を付与（HTTP API のルート単位オーソライザ）。公開ルートは従来どおり無認可。
- SAM 定義（抜粋・イメージ）:
```yaml
  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: !Ref Stage
      Auth:
        Authorizers:
          CognitoJwt:
            IdentitySource: "$request.header.Authorization"
            JwtConfiguration:
              issuer: !Sub
                - "https://cognito-idp.${AWS::Region}.amazonaws.com/${UP}"
                - UP: !ImportValue
                    "Fn::Sub": "iyf-${Stage}-UserPoolId"
              audience:
                - !ImportValue
                    "Fn::Sub": "iyf-${Stage}-UserPoolClientId"
        # DefaultAuthorizer は設定しない（公開ルートを無認可に保つ）
      CorsConfiguration:
        AllowMethods: [GET, POST, PUT, DELETE, OPTIONS]
        AllowHeaders: [content-type, authorization]
        AllowOrigins: !Split [",", !Ref AllowedOrigins]   # admin/public 共通オリジン集合
      DefaultRouteSettings: { ThrottlingBurstLimit: 20, ThrottlingRateLimit: 10 }
```
> 注: 管理系のオリジン（admin-web）は `AllowedOrigins` に追加。CloudFront 側で admin と public を分離する場合はオリジン集合に両方を含める（U5 と調整）。

## 3. AdminFunction（管理ハンドラ Lambda）

```yaml
  AdminFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: src.handlers.admin.handler
      Description: Admin APIs (Phase 2) — content/calendar/contact admin + auth/users
      Environment:
        Variables:
          USER_POOL_ID: !ImportValue { "Fn::Sub": "iyf-${Stage}-UserPoolId" }
      Policies:
        - DynamoDBCrudPolicy: { TableName: !Ref PostsTable }
        - DynamoDBCrudPolicy: { TableName: !Ref NoticesTable }
        - DynamoDBCrudPolicy: { TableName: !Ref EventsTable }
        - DynamoDBCrudPolicy: { TableName: !Ref InquiriesTable }
        - DynamoDBCrudPolicy: { TableName: !Ref UsersTable }
        # cognito-idp Admin 操作（UserPool ARN 限定, SECURITY-06）
        - Statement:
            - Effect: Allow
              Action:
                - cognito-idp:AdminCreateUser
                - cognito-idp:AdminAddUserToGroup
                - cognito-idp:AdminDisableUser
                - cognito-idp:AdminEnableUser
                - cognito-idp:AdminGetUser
                - cognito-idp:ListUsers
              Resource: !Sub
                - "arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${UP}"
                - UP: !ImportValue { "Fn::Sub": "iyf-${Stage}-UserPoolId" }
        - Statement:
            - Effect: Allow
              Action: [ssm:GetParameter]
              Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/iyf/${Stage}/*"
      Events:
        # 記事
        CreatePost:   { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: POST,   Path: /admin/posts,            Auth: { Authorizer: CognitoJwt } } }
        ListPostsAdm: { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: GET,    Path: /admin/posts,            Auth: { Authorizer: CognitoJwt } } }
        GetPostAdm:   { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: GET,    Path: /admin/posts/{id},       Auth: { Authorizer: CognitoJwt } } }
        UpdatePost:   { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: PUT,    Path: /admin/posts/{id},       Auth: { Authorizer: CognitoJwt } } }
        DeletePost:   { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: DELETE, Path: /admin/posts/{id},       Auth: { Authorizer: CognitoJwt } } }
        SetPostStat:  { Type: HttpApi, Properties: { ApiId: !Ref HttpApi, Method: PUT,    Path: /admin/posts/{id}/status,Auth: { Authorizer: CognitoJwt } } }
        # お知らせ（同型: /admin/notices ...）
        # カレンダー: POST/GET/PUT/DELETE /admin/events
        # 問い合わせ: GET /admin/inquiries, GET /admin/inquiries/{id}, PUT /admin/inquiries/{id}/status
        # ユーザー: POST /admin/users/invite, GET /admin/users, PUT /admin/users/{id}/status, PUT /admin/me/profile
```
> 全管理ルートに `Auth: { Authorizer: CognitoJwt }`。ロール/オーナー認可はアプリ層（`common/auth.py`）。

## 4. DynamoDB 変更（GSI 追加）

### Posts / Notices — `GSI-status`（draft含む管理系一覧）
- 追加属性: `status`（S, 常時 "draft"/"published"）, `updated_at_epoch`（N, 常時）。
- 追加 GSI: `GSI-status` = HASH:`status`, RANGE:`updated_at_epoch`（降順読み）。Projection: ALL（一覧に必要な要約項目を含むため。データ小のためコスト影響軽微）。
- 既存 `GSI-published`（sparse: gsi_status を published のみ設定）は**公開系専用として維持**。
- 移行注意: 既存 Post/Notice レコードに `status`/`updated_at_epoch` 属性が無い場合、GSI に載らない。**Phase 2 デプロイ時に既存レコードへ属性バックフィル**（U4 移行分含む）を実施（Code Generation / Build&Test で 1回スクリプト）。

### Inquiries — `GSI-status`（listInquiries by status）
- 追加属性: `status`（S, 常時 new/in_progress/done）。`created_at_epoch` は既存。
- 追加 GSI: `GSI-status` = HASH:`status`, RANGE:`created_at_epoch`。Projection: ALL。
- 既存 `GSI-dedup` は維持。

### Users
- GSI 追加なし。listUsers は Scan（≤10, admin・低頻度）。email 一意性は Cognito 担保。

## 5. セキュリティ（Phase 2 有効化）

| 項目 | 対応 |
|---|---|
| SECURITY-06 | AdminFunction ロールは対象テーブル/GSI/UserPool ARN/SSM プレフィックス限定。ワイルドカード禁止 |
| SECURITY-08 | 管理ルートは JWT オーソライザ必須（layer1）＋アプリ層ロール/オーナー認可（layer2, IDOR）。CORS オリジン限定 |
| SECURITY-11 | 既存 DefaultRouteSettings スロットリング適用。招待は軽い上限（アプリ層/将来 usage plan） |
| SECURITY-12 | Cognito(U5): TOTP・AllowAdminCreateUserOnly・AdvancedSecurity ENFORCED。Admin MFA 強制は U5 で最終化 |
| SECURITY-13/14 | AdminFunction 監査ログ、認可失敗ログ、90日保持、ログ削除権限なし |

## 6. コスト（Phase 2 増分）
- AdminFunction: 低頻度・無料枠内が大半（ほぼ0円）。
- GSI 3本（Posts/Notices/Inquiries status）: 小容量・On-Demand で数十円未満。
- Cognito: MAU≤10 無料枠（0円）。
- → Phase 2 でも **月 数百円規模**を維持（NFR-COST-01）。

## 7. トレーサビリティ
- 反映: functional-design(`*-admin.md`), nfr-design(`*-phase2.md`), 現行 template.yaml×2
- 対応 SECURITY: 06/08/11/12/13/14
- 申し送り: `../../shared-infrastructure.md`（Phase 2 追記: Admin MFA 強制・Token 有効期限明示・初期adminブートストラップ）
