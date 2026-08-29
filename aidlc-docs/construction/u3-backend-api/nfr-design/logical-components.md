# Logical Components — U3 backend-api（IYフレンズ）

U3 backend-api を実現する論理コンポーネントと、それらの連携・インフラ要素を定義する。
物理的なインフラ確定（リソース名・ARN・IaC）は **Infrastructure Design** で行う。ここでは論理構成のみ。

方針: 最小構成（キュー・DAX・専用キャッシュ層は導入しない）。同期処理中心。

---

## 1. 論理コンポーネント一覧（U3 内部モジュール）

| モジュール | 役割 | 主なエンティティ | 主な依存 |
|---|---|---|---|
| **common** | 認証/認可、入力検証、構造化ロギング、エラーハンドリング、DynamoDBアクセス層（リポジトリ）、監査ログ | User（Cognito連携） | Cognito, DynamoDB, Secrets Manager |
| **content** | ブログ記事・お知らせの CRUD／公開制御・一覧・詳細 | Post, Notice | common, DynamoDB |
| **calendar** | イベントの CRUD／一覧・詳細 | Event | common, DynamoDB |
| **contact** | 問い合わせ受付（保存＋SES通知）、状態管理（未対応/対応中/対応済） | Inquiry | common, DynamoDB, SES |

> auth モジュールは Phase 2（管理CMS）で本格化。Phase 1 は common に最小限の Cognito トークン検証のみ含む。

## 2. アプリ層の論理構造（各モジュール共通）

```
[API Gateway (HTTP API)]
        │  (JWT/認可, スロットリング, キャッシュ)
        ▼
[Lambda Handler]  ── common.guard(認証/認可) ── common.validate(Pydantic)
        │
        ▼
[Service (module business logic)]  ── 状態機械/ビジネスルール(BR-*)
        │
        ▼
[Repository (common data-access)]  ── パラメータ化 Query/GetItem/PutItem
        │
        ▼
[DynamoDB (On-Demand, PITR, 暗号化)]
```

- 横断: `common.logger`（相関ID・PIIマスク）, `common.error_handler`（グローバル例外・fail-closed）, `common.audit`（重要変更記録）

## 3. インフラ論理要素（Logical Infrastructure Elements）

| 要素 | 用途 | 採否 | 備考 |
|---|---|---|---|
| **API Gateway (HTTP API)** | API公開・認可・スロットリング・キャッシュ | 採用 | REST APIより低コスト。SECURITY-11 レート制限 |
| **Lambda** | 各モジュールの実行 | 採用 | ステートレス・従量 |
| **DynamoDB (On-Demand)** | データ永続化 | 採用 | PITR有効、保存時暗号化 |
| **Cognito** | 管理者/編集者認証、MFA、ブルートフォース対策 | 採用 | SECURITY-12 |
| **SES** | 問い合わせ通知メール（同期送信） | 採用 | Q-D1=A。ベストエフォート |
| **Secrets Manager / SSM SecureString** | 秘密情報保管 | 採用（Infraで最終選定） | 平文禁止（SECURITY-12） |
| **CloudWatch Logs / Alarms** | 集中ログ・アラート | 採用 | 保持90日、SECURITY-03/14 |
| SQS（非同期通知キュー） | — | **不採用** | Q-D1=A（同期送信）。将来必要時に追加可 |
| DAX（専用キャッシュ） | — | **不採用** | Q-D3=A。CDN/APIGWキャッシュで代替 |
| プロビジョンド同時実行 | — | **不採用** | コスト最適化 |
| マルチリージョン/グローバルテーブル | — | **不採用** | Q-N3=A 単一リージョン |

## 4. 主要データフロー

### 4.1 公開読み取り（例: 記事一覧）
```
利用者 → CloudFront(cache) → API Gateway(cache, throttle) → Lambda(content) → Repository → DynamoDB(Query, 公開のみ, 10件/ページ)
```
- キャッシュヒット時は Lambda/DynamoDB に到達せず高速・低コスト。

### 4.2 問い合わせ送信（DB先行＋同期通知, Q-D1=A / Q-D2=A）
```
利用者 → API Gateway(throttle) → Lambda(contact)
   1. validate(Pydantic, SECURITY-05)
   2. 軽量冪等チェック（同一 email+message の短時間重複を無視）
   3. DynamoDB PutItem（Inquiry: 未対応）   ← ここまで成立で受付完了
   4. SES 同期送信（失敗はログ＋通知ステータス記録, エラーにしない）
   5. 汎用成功応答
```
- fail-closed: 1〜3のいずれか失敗時は受付失敗として汎用エラー応答（SECURITY-15）。4の失敗のみ受付は成立扱い。

### 4.3 管理系（投稿/状態変更, Phase 1でAPI定義, Phase 2でUI）
```
編集者/管理者 → API Gateway → Lambda(content/contact)
   1. common.guard: Cognitoトークン検証 + ロール/オーナー確認（SECURITY-08, IDOR防止）
   2. validate
   3. 状態機械に従い遷移（BR-STATE）
   4. DynamoDB 更新 + common.audit（actor/timestamp/before-after, SECURITY-13）
```

## 5. コンポーネント間の非機能連携

| 連携 | 適用パターン |
|---|---|
| Handler ↔ common.guard | 全ミューテーション/保護エンドポイントでガード必須（deny-by-default, SECURITY-08） |
| Service ↔ Repository | パラメータ化アクセスのみ（SECURITY-05）、最小権限ロール（SECURITY-06） |
| 全外部呼び出し | bounded retry + fail-closed + 例外ハンドリング（SECURITY-15） |
| 全ハンドラ | 構造化ログ（相関ID, PIIマスク, SECURITY-03） |

## 6. 後段への申し送り（Infrastructure Design）

- 各論理要素 → 物理リソース（テーブル名、GSI、IAMポリシー、API Gatewayステージ/スロットリング値、SESドメイン検証、Secrets Manager vs SSM、CloudWatch保持90日/アラーム閾値）
- SECURITY-02/07/09/10 の成果物レベル担保
