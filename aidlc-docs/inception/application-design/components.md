# コンポーネント定義 (Components) — IYフレンズ公式サイト

設計判断（application-design-plan.md 回答）:
- 描画方式: **SSG中心**（公開サイト）（Q-A1=A）
- 公開/管理: **別アプリに分離**（Q-A2=A）
- 入力形式: **リッチテキスト(WYSIWYG)**（Q-A3=A）
- 既存記事: **スクレイピングで収集**（Q-A4=A）
- データ: **DynamoDB おまかせ**（Q-A5=A）
- リポジトリ: **ポリレポ（層ごと別リポジトリ）**（Q-A6=B）

> 本ドキュメントは高レベルのコンポーネント責務・インターフェースを定義する。詳細な業務ルール・データモデルは Construction/Functional Design（ユニット単位）で確定する。

---

## コンポーネント全体像（層別）

| レイヤ | コンポーネント | リポジトリ（ポリレポ） |
|---|---|---|
| フロント（公開） | PublicWebApp | `iyf-public-web` |
| フロント（管理） | AdminWebApp | `iyf-admin-web` |
| バックエンド | BackendApi（ContentService/CalendarService/ContactService/AuthService を内包） | `iyf-backend-api` |
| データ移行 | BlogMigrationTool | `iyf-backend-api`（バッチ/スクリプトとして同梱） |
| インフラ | InfrastructureStack（CDK） | `iyf-infra` |

---

## C1. PublicWebApp（公開フロントエンド）
- **目的**: 一般閲覧者・入部検討者向けの公開サイトUI（ログイン不要）
- **責務**:
  - 紹介/沿革/規約などの静的ページ表示（SSGでビルド時生成）
  - ブログ「スタッフの声」一覧・アーカイブ・詳細の表示
  - お知らせ一覧・詳細の表示
  - 活動予定カレンダーの表示
  - メンバー募集案内の表示
  - お問い合わせフォーム（送信）
  - apple-design 基調・レスポンシブ・`prefers-reduced-motion` 対応
- **インターフェース（消費するAPI）**: PublicApi（読み取り専用）＋ ContactApi（送信）
- **非対象**: 認証・投稿・管理機能（AdminWebApp が担当）
- **対応ストーリー**: US-01〜06, 08, 10, 12, 13, 17

## C2. AdminWebApp（管理フロントエンド / CMS）
- **目的**: 管理者・編集者向けの管理CMS UI（認証必須・**スマホ最適化**）
- **責務**:
  - ログイン（Cognito）・MFA・ログアウト
  - ブログ/お知らせの作成・編集・削除・公開/下書き管理（WYSIWYG）
  - カレンダー予定の登録・編集
  - 問い合わせ一覧・詳細・対応状況管理
  - 編集者の招待・アカウント管理（管理者のみ）
  - 役割（Admin/Editor）に応じたUI出し分け
- **インターフェース（消費するAPI）**: AdminApi（認証必須）
- **対応ストーリー**: US-07, 09, 11, 14, 15, 16, 18

## C3. BackendApi（サーバーレスAPI・Python）
公開/管理の2系統のAPIを提供し、内部を機能サービスに分割する。API入口は認可境界で分離（PublicApiGateway / AdminApiGateway）。

### C3-a. ContentService
- **目的**: ブログ・お知らせ・静的ページコンテンツの管理
- **責務**: 記事/お知らせの CRUD、公開/下書き状態管理、一覧/詳細取得、カテゴリ（単一ブログ「スタッフの声」）
- **公開API**: 記事一覧/詳細/アーカイブ、お知らせ一覧/詳細（公開分のみ）
- **管理API**: 記事/お知らせの作成・更新・削除・公開制御

### C3-b. CalendarService
- **目的**: 活動予定（練習/試合等）の管理
- **責務**: 予定の CRUD、公開カレンダー取得
- **公開API**: 予定一覧取得（期間指定）
- **管理API**: 予定の作成・更新・削除

### C3-c. ContactService
- **目的**: お問い合わせの受付・保存・通知・履歴管理
- **責務**: 入力検証、問い合わせ永続化、SES通知、履歴一覧、対応状況更新、レート制限/スパム対策
- **公開API**: 問い合わせ送信
- **管理API**: 問い合わせ一覧/詳細/状態更新

### C3-d. AuthService
- **目的**: 認証・認可・アカウント運用
- **責務**: Cognito 連携、トークン検証、ロール（Admin/Editor）判定、編集者招待、アカウント無効化
- **管理API**: 招待、ユーザー一覧、ロール/状態変更（Adminのみ）
- **横断**: 全 AdminApi のリクエストで認可を強制（SECURITY-08/12）

## C4. BlogMigrationTool（データ移行）
- **目的**: 現行サイトの既存ブログ記事（約339件）を新DBへ取り込む
- **責務**: 現行サイトからの収集（スクレイピング, Q-A4=A）、正規化（タイトル/本文/投稿日/著者）、ContentService 経由での投入。**写真は当面除外**（Q14）
- **形態**: バックエンドのバッチ/スクリプト（一度きり〜再実行可能）
- **対応ストーリー**: US-06

## C5. InfrastructureStack（IaC / CDK）
- **目的**: AWS リソースの定義・デプロイ
- **責務**: S3+CloudFront（公開/管理配信）、API Gateway、Lambda、DynamoDB、Cognito、SES、IAM（最小権限）、CloudWatch（ログ/アラート）
- **横断**: セキュリティベースライン（暗号化・ログ・ヘッダ・最小権限）を担保
- **対応ストーリー**: US-18, US-19

---

## API 境界（認可分離）
| 入口 | 認証 | 用途 | 消費者 |
|---|---|---|---|
| **PublicApi**（PublicApiGateway） | 不要 | 公開コンテンツ読み取り＋問い合わせ送信 | PublicWebApp |
| **AdminApi**（AdminApiGateway） | 必須（Cognito/JWT検証） | 投稿・管理・アカウント運用 | AdminWebApp |

> セキュリティ: PublicApi は読み取り＋問い合わせ送信のみ（書き込みは限定）。AdminApi は全経路でトークン検証・ロール認可・CORSオリジン限定（SECURITY-05/08/12）。
