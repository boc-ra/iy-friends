# アプリケーション設計 統合ドキュメント (Application Design) — IYフレンズ公式サイト

本ドキュメントは以下の設計成果物を統合したものである。
- `components.md`（コンポーネント定義）
- `component-methods.md`（メソッド署名）
- `services.md`（サービス層）
- `component-dependency.md`（依存関係・データフロー）

---

## 1. 設計判断サマリ（application-design-plan.md 回答）
| 項目 | 決定 |
|---|---|
| 描画方式（公開） | **SSG中心**（SEO・速度・低コスト）（Q-A1=A） |
| 公開/管理の分離 | **別フロントアプリに分離**（Q-A2=A） |
| 入力形式 | **リッチテキスト(WYSIWYG)**（Q-A3=A） |
| 既存記事の入手 | **現行サイトからスクレイピング**（Q-A4=A、画像は当面除外） |
| DynamoDB 設計 | **おまかせ**（小規模・低コスト最適化）（Q-A5=A） |
| リポジトリ構成 | **ポリレポ（層ごと別リポジトリ）**（Q-A6=B） |

## 2. アーキテクチャ概要
- **フロント**: React + TypeScript。公開＝SSG（S3+CloudFront配信）、管理＝認証必須SPA
- **バックエンド**: Python サーバーレス（API Gateway + Lambda）。Public/Admin を認可境界で分離
- **データ**: DynamoDB（保存/転送暗号化）、認証＝Cognito、メール＝SES
- **配信/インフラ**: S3 + CloudFront、CDK による IaC、CloudWatch 監視
- **リリース**: 2段階（Phase 1 公開サイト / Phase 2 管理CMS）

## 3. コンポーネント（要約）
| ID | コンポーネント | 責務 | リポジトリ |
|---|---|---|---|
| C1 | PublicWebApp | 公開サイトUI（閲覧・問い合わせ送信） | iyf-public-web |
| C2 | AdminWebApp | 管理CMS UI（投稿・管理・招待、スマホ最適化） | iyf-admin-web |
| C3 | BackendApi（Content/Calendar/Contact/Auth） | サーバーレスAPI | iyf-backend-api |
| C4 | BlogMigrationTool | 既存記事の移行（スクレイピング） | iyf-backend-api |
| C5 | InfrastructureStack | AWS リソース定義（CDK） | iyf-infra |

（詳細は `components.md`）

## 4. サービス層（要約）
- **ContentService**: ブログ/お知らせ/静的ページの管理・公開
- **CalendarService**: 活動予定の管理・公開
- **ContactService**: 問い合わせ受付・保存・SES通知・履歴管理
- **AuthService**: 認証/認可・編集者招待・アカウント運用（Cognito）

主要オーケストレーション：公開読取／問い合わせ送信／管理操作（認可前段）／編集者招待／ブログ移行（詳細は `services.md`）。

## 5. メソッド概要
各サービスの公開API/管理APIメソッドを `component-methods.md` に定義（例：`listPosts`/`getPost`/`createPost`/`submitInquiry`/`inviteEditor`/`authorizeRequest` 等）。**詳細な業務ルール・データモデルは Construction/Functional Design で確定**。

## 6. 依存関係・データフロー
- 公開: PublicWebApp → PublicApiGateway → Content/Calendar/Contact → DynamoDB（+SES）
- 管理: AdminWebApp →(Cognito)→ AdminApiGateway →(AuthService認可)→ 各サービス → DynamoDB（+監査ログ）
- 循環依存なし（詳細・図は `component-dependency.md`）

## 7. セキュリティ設計の反映（Security Baseline: ブロッキング）
| ルール | 設計での担保 |
|---|---|
| SECURITY-01 | DynamoDB/S3 暗号化、全通信 TLS |
| SECURITY-04 | 配信に CSP/HSTS 等セキュリティヘッダ |
| SECURITY-05 | 全API入力のスキーマ検証・サニタイズ |
| SECURITY-06 | Lambda/IAM 最小権限 |
| SECURITY-08 | AdminApi 全経路で認可・IDOR対策・CORS限定 |
| SECURITY-11 | 認可を共通前段に分離、公開APIにレート制限 |
| SECURITY-12 | Cognito、管理者MFA、秘密情報は Secrets Manager |
| SECURITY-13/14 | 管理変更の監査ログ、認証/認可失敗のアラート |
| SECURITY-15 | 外部呼び出しのエラーハンドリング・fail-closed |

## 8. PII・プライバシー方針
- 子供の氏名は掲載しない／個人特定されない範囲（DR-05）。本文サニタイズと運用ルールで担保。
- 初期リリースでは写真掲載なし（MediaService は将来有効化）。

## 9. 設計の完全性・整合性チェック
- [x] 全ユーザーストーリー（US-01〜19）に対応コンポーネントが存在
- [x] 公開/管理の認可境界が定義済み（API Gateway 分離）
- [x] 2段階リリースへコンポーネントを割当済み
- [x] セキュリティベースラインを設計に反映
- [x] 循環依存なしを確認
- [x] データフロー（Mermaid＋テキスト代替）を提示

## 10. 次段階への申し送り（Units Generation / Functional Design 向け）
- ユニット候補: 公開フロント / 管理フロント / Contentサービス / Calendarサービス / Contactサービス / Authサービス / 移行ツール / インフラ
- Functional Design で確定すべき項目: 各データモデル（Posts/Notices/Events/Inquiries/Users）、状態遷移（下書き/公開、問い合わせ対応状況）、バリデーション詳細、DynamoDB キー設計（おまかせ方針で提案）
