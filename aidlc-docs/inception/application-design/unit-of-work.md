# ユニット定義 (Unit of Work) — IYフレンズ公式サイト

分解方針（unit-of-work-plan.md 回答）:
- バックエンド: **モジュラーモノリス**（1サービス／内部モジュール分割）（Q-U1=A）
- フロント: **公開/管理を別ユニット**（Q-U2=A）
- 実装順序: **Phase 1 先行 → Phase 2**（Q-U3=A）
- 移行ツール: **独立ユニット**（Q-U4=A）
- リポジトリ: **ポリレポ**（層ごと別リポジトリ）（Q-A6=B）

---

## ユニット一覧

### U1: public-web（公開フロントエンド）
- **種別**: Frontend Service（SSG）
- **責務**: 公開サイトUI（紹介/規約/ブログ/お知らせ/カレンダー/募集/問い合わせ送信）。apple-design・レスポンシブ
- **技術**: React + TypeScript（SSG：Next.js静的出力 または Vite+プリレンダリング）
- **消費API**: PublicApi（読取）＋問い合わせ送信
- **Phase**: 1
- **リポジトリ**: `iyf-public-web`
- **含むコンポーネント**: PublicWebApp(C1)

### U2: admin-web（管理フロントエンド / CMS）
- **種別**: Frontend Service（認証SPA）
- **責務**: ログイン(Cognito/MFA)、ブログ/お知らせ投稿（WYSIWYG）、カレンダー登録、問い合わせ管理、編集者招待。**スマホ最適化**
- **技術**: React + TypeScript（SPA）
- **消費API**: AdminApi（認証必須）
- **Phase**: 2
- **リポジトリ**: `iyf-admin-web`
- **含むコンポーネント**: AdminWebApp(C2)

### U3: backend-api（バックエンド・モジュラーモノリス）
- **種別**: Backend Service（サーバーレス・Python）
- **責務**: 公開/管理API。内部を論理モジュールに分割：
  - `content` モジュール（ブログ/お知らせ/静的ページ）
  - `calendar` モジュール（活動予定）
  - `contact` モジュール（問い合わせ・SES通知・履歴）
  - `auth` モジュール（認可・招待・Cognito連携）
  - `common` モジュール（入力検証・ロギング・エラー処理・認可前段）
- **入口**: PublicApiGateway（公開）/ AdminApiGateway（認証）
- **技術**: Python（Lambda）、API Gateway、DynamoDB、SES、Cognito
- **Phase**: 1（公開読取・問い合わせ送信）＋ 2（管理・認証）
- **リポジトリ**: `iyf-backend-api`
- **含むコンポーネント**: ContentService/CalendarService/ContactService/AuthService(C3)

### U4: blog-migration（移行バッチ）
- **種別**: Batch/Tool
- **責務**: 現行サイトから既存記事（約339件）を収集→正規化→投入（画像除外）。一度きり〜再実行可
- **技術**: Python スクリプト（U3 の content モジュール経由で投入）
- **Phase**: 1
- **リポジトリ**: `iyf-backend-api`（同梱、`migration/` 配下）
- **含むコンポーネント**: BlogMigrationTool(C4)

### U5: infra（IaC / CDK）
- **種別**: Infrastructure（IaC）
- **責務**: AWS リソース定義・デプロイ（S3/CloudFront/APIGW/Lambda/DynamoDB/Cognito/SES/IAM最小権限/CloudWatch）。セキュリティベースライン担保
- **技術**: AWS CDK（TypeScript または Python）
- **Phase**: 1（公開系）＋ 2（管理/認証系の追加）
- **リポジトリ**: `iyf-infra`
- **含むコンポーネント**: InfrastructureStack(C5)

---

## コード配置戦略（Greenfield / ポリレポ）

Q-A6=B（層ごと別リポジトリ）に基づき、ユニット＝リポジトリで分離する。

```
iyf-public-web/        # U1 公開フロント（SSG）
  src/  (pages, components, api-client, styles[apple-design])
  public/
  package.json

iyf-admin-web/         # U2 管理フロント（認証SPA）
  src/  (pages, components, auth[cognito], editor[wysiwyg], api-client)
  package.json

iyf-backend-api/       # U3 バックエンド（モジュラーモノリス）＋ U4 移行
  src/
    content/           # ブログ・お知らせ・静的
    calendar/          # 活動予定
    contact/           # 問い合わせ・SES
    auth/              # 認可・招待・Cognito
    common/            # 検証・ログ・エラー・認可前段
    handlers/          # API Gateway ハンドラ(public/admin)
  migration/           # U4 移行バッチ
  tests/               # unit / PBT(部分適用)
  pyproject.toml (lock)

iyf-infra/             # U5 IaC(CDK)
  lib/  (stacks: frontend, api, data, auth, monitoring)
  bin/
```

> 注: AI-DLC の「アプリケーションコードはワークスペース直下」の原則に従い、各リポジトリはワークスペースルート配下に配置する（`aidlc-docs/` にはコードを置かない）。ポリレポの各リポジトリ間はAPI契約で連携する。

## ユニット境界・検証
- [x] 全ストーリー（US-01〜19）がいずれかのユニットに割当済み（`unit-of-work-story-map.md` 参照）
- [x] 公開/管理の認可境界がユニット/API入口で分離
- [x] 2段階リリースにユニットを整合
- [x] バックエンドはモジュラーモノリスで低コスト運用
- [x] 循環依存なし（`unit-of-work-dependency.md` 参照）
