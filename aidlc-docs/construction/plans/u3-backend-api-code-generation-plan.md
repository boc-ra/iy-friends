# Code Generation 計画 — U3 backend-api（IYフレンズ / Phase 1）

本計画は U3 backend-api の **Phase 1 スコープ**（公開読み取りAPI＋問い合わせ送信＋共通基盤）のコード生成を、明示的な番号付きステップで定義する。**この計画がCode Generationの唯一の正**とする。

---

## 1. ユニットコンテキスト

- **プロジェクト種別**: Greenfield / ポリレポ
- **アプリコード配置（ワークスペース直下）**: `C:\Users\syuto\IY FRIENDS\iyf-backend-api\`（`aidlc-docs/` には置かない）
- **ドキュメント配置**: `aidlc-docs/construction/u3-backend-api/code/`（Markdown要約のみ）
- **言語/実行**: Python 3.13 / AWS Lambda、IaC=AWS SAM
- **アーキテクチャ**: モジュラモノリス（content / calendar / contact / common / handlers）
- **依存ユニット**: U5(SES/Cognito/共有インフラ)＝基盤提供、U4＝移行データ投入（U3はデータを配信）。U1＝APIコンシューマ（契約提供側がU3）

### 対象ディレクトリ構成（Phase 1で生成）
```
iyf-backend-api/
  src/
    common/       # 検証・ログ・エラー・設定(SSM)・DynamoDB基盤・認可前段
    content/      # ブログ・お知らせ（読み取り）
    calendar/     # 活動予定（読み取り）
    contact/      # 問い合わせ（送信・保存・SES）
    handlers/     # API Gateway ハンドラ（public）
  tests/          # unit + PBT(部分適用)
  template.yaml   # AWS SAM（API/Lambda/DynamoDB/IAM/Logs）
  samconfig.toml
  pyproject.toml + ロックファイル
  README.md
```

### Phase 1 実装ストーリー（担当分）
- [x] US-01 トップ最新情報（content 読み取り）
- [x] US-04 ブログ一覧/アーカイブ（content）
- [x] US-05 ブログ詳細（content）
- [x] US-06 既存ブログ移行閲覧の配信（content：U4が投入したデータを配信）
- [x] US-08 お知らせ閲覧（content）
- [x] US-10 カレンダー閲覧（calendar）
- [x] US-13 問い合わせ送信（contact＋SES）
- [x] US-18 セキュリティ（横断：検証・認可前段・ログ・エラー）
- [x] US-19 低コスト運用（横断：サーバーレス最小構成）

### Phase 2 に先送り（本計画では**対象外**）
- US-07/09 投稿、US-11 カレンダー登録、US-14 問い合わせ管理（管理系書き込み）
- US-15/16 ログイン・編集者招待（auth モジュール、Cognito 連携本実装）
- `src/auth/` と `handlers/` の admin 系、`migration/`（U4）

---

## 2. 生成ステップ（番号順・チェックボックス）

### Step 1: プロジェクト構成セットアップ（Greenfield）
- [x] `iyf-backend-api/` スケルトン作成（上記ディレクトリ）
- [x] `pyproject.toml`＋ロックファイル（依存固定, SECURITY-10）：boto3, pydantic v2, （dev: pytest, hypothesis, moto）
- [x] `.gitignore`, `README.md`（雛形）
- 対応: US-19

### Step 2: common モジュール生成
- [x] `common/config.py`（SSM Parameter Store SecureString 読取, 環境変数）
- [x] `common/logging.py`（構造化JSONログ・相関ID・PIIマスク, SECURITY-03）
- [x] `common/errors.py`（例外型・グローバルエラーハンドラ・fail-closed・汎用メッセージ, SECURITY-15/09）
- [x] `common/validation.py`（Pydantic基盤・共通バリデータ, SECURITY-05）
- [x] `common/auth.py`（認可前段：公開/保護判定・Cognito JWT検証の入口。Phase 1は公開判定中心, SECURITY-08）
- [x] `common/db.py`（DynamoDBクライアント・リポジトリ基底・パラメータ化アクセス・limitedリトライ）
- [x] `common/audit.py`（重要変更の監査ログ雛形, SECURITY-13）
- 対応: US-18/19

### Step 3: common ユニットテスト（＋PBT部分適用）
- [x] `tests/common/` 検証・ログマスク・エラー整形のテスト
- [x] PBT：純粋関数（バリデータ/整形）・シリアライズ往復（モデル⇔dict）

### Step 4: common 要約
- [x] `aidlc-docs/construction/u3-backend-api/code/common-summary.md`

### Step 5: ビジネスロジック生成（ドメインモデル＋サービス）
- [x] `content/models.py`（Post, Notice：Pydantic, status=draft/published）
- [x] `content/service.py`（公開一覧/詳細取得, 公開状態フィルタ, ページング10件, BR-STATE/BR-VAL）
- [x] `calendar/models.py`（Event）＋ `calendar/service.py`（日付順一覧/詳細）
- [x] `contact/models.py`（Inquiry：name/email/message, status=未対応/対応中/対応済）
- [x] `contact/service.py`（受付：軽量冪等→保存→SES同期通知(ベストエフォート), BR-CONTACT/BR-SEC）
- 対応: US-01/04/05/06/08/10/13

### Step 6: ビジネスロジック ユニットテスト（＋PBT）
- [x] `tests/content/` `tests/calendar/` `tests/contact/`（状態遷移・公開フィルタ・冪等・バリデーション）
- [x] PBT：モデル⇔DynamoDBアイテムのシリアライズ往復、日付/カテゴリ整形

### Step 7: ビジネスロジック要約
- [x] `aidlc-docs/construction/u3-backend-api/code/business-logic-summary.md`

### Step 8: リポジトリ層生成
- [x] `content/repository.py`（Posts/Notices：GetItem/Query GSI公開・日付順）
- [x] `calendar/repository.py`（Events：Query GSI日付）
- [x] `contact/repository.py`（Inquiries：PutItem/Query/短時間重複チェック）
- [x] いずれも最小権限前提・Scan回避・パラメータ化（SECURITY-05/06）

### Step 9: リポジトリ層 ユニットテスト
- [x] `tests/**/repository` を moto（DynamoDBモック）で検証

### Step 10: リポジトリ層 要約
- [x] `aidlc-docs/construction/u3-backend-api/code/repository-summary.md`

### Step 11: APIレイヤ生成（public ハンドラ）
- [x] `handlers/public.py`：
  - GET 記事一覧/詳細、お知らせ一覧/詳細（content）
  - GET イベント一覧/詳細（calendar）
  - POST 問い合わせ（contact）
- [x] 各ハンドラ：入力検証（SECURITY-05）→ 公開/認可判定（SECURITY-08）→ サービス呼び出し → 汎用エラー整形（SECURITY-15）
- [x] CORSオリジン限定、レスポンスに最小セキュリティヘッダ
- 対応: US-01/04/05/06/08/10/13/18

### Step 12: APIレイヤ ユニットテスト
- [x] `tests/handlers/`（正常・検証エラー・404・レート/サイズ上限・エラー整形）

### Step 13: APIレイヤ 要約
- [x] `aidlc-docs/construction/u3-backend-api/code/api-layer-summary.md`

### Step 14: データベース定義（マイグレーション相当）
- [x] DynamoDBテーブル定義は SAM `template.yaml` に含める（Posts/Notices/Events/Inquiries/Users, PITR/SSE/On-Demand/GSI）
- [x] 注: 実データ投入（既存ブログ移行）は U4 の `migration/` が担当（本計画対象外）

### Step 15: デプロイ成果物生成
- [x] `template.yaml`（SAM：HTTP API＋スロットリング＋アクセスログ、Lambda(python3.13)、DynamoDB×5、最小権限IAM、CloudWatch LogGroup 保持90日＋アラーム、SSM参照）
- [x] `samconfig.toml`（prodステージ, ap-northeast-1）
- [x] CI：依存脆弱性スキャン／SBOM 生成の設定雛形（SECURITY-10）
- 対応: US-18/19

### Step 16: ドキュメント生成
- [x] `iyf-backend-api/README.md`（構成・ビルド/デプロイ・環境）
- [x] `aidlc-docs/construction/u3-backend-api/code/api-documentation.md`（Phase 1 公開API契約：エンドポイント/リクエスト/レスポンス）
- [x] `aidlc-docs/construction/u3-backend-api/code/code-generation-summary.md`（生成物一覧・ストーリー対応・セキュリティ適合）

---

## 3. セキュリティ適合（コード層で担保する主項目）
- SECURITY-05（入力検証）, 08（認可・IDOR防止・CORS）, 03（構造化ログ・PII非出力）, 06（最小権限・パラメータ化）, 11（認可集約・レート制限前提）, 13（監査）, 15（fail-closed・グローバルエラー）
- SECURITY-10（依存固定・脆弱性スキャン・SBOM）＝Step1/15
- Phase 2 で auth 本実装時に 12（認証）を完成

## 4. トレーサビリティ
- ストーリー: US-01/04/05/06/08/10/13（主, Phase1）＋ US-18/19（横断）
- 設計参照: `../u3-backend-api/functional-design/*`, `../nfr-design/*`, `../infrastructure-design/*`
- 総ステップ数: 16（うちテスト/要約/デプロイ/文書を含む）
