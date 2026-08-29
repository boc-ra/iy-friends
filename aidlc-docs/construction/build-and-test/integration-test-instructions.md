# Integration Test Instructions — IYフレンズ Phase 1

## 目的
ユニット間（フロント U1 ↔ バックエンド U3 ↔ データ DynamoDB / 移行 U4 / 配信 U5）の連携を検証する。

## テストシナリオ

### S1: U3 API ↔ DynamoDB（backend結合）
- **説明**: 公開読み取り・問い合わせ保存がDynamoDBと正しく連携するか
- **セットアップ**: `sam local start-api`（Docker）＋ DynamoDB Local、または開発用AWSスタックへ `sam deploy`
- **手順**:
  1. `GET /posts` → 公開記事のみ・10件・カーソルが返る
  2. `GET /posts/{id}`（draft）→ 404
  3. `POST /contact`（name/email/message）→ 201・Inquiries に保存・SESは検証環境ではモック/サンドボックス
- **期待**: ステータス/本文がAPI契約（`u3-backend-api/code/api-documentation.md`）と一致
- **クリーンアップ**: 開発スタック削除 or DynamoDB Local 停止

### S2: U4 移行 → U3 Posts（データ投入）
- **手順**:
  1. `migration/config.toml` にサンプルサイト or フィクスチャを設定
  2. `python -m migration.run --config migration/config.toml --dry-run --limit 5` → 件数/正規化確認
  3. 本投入後、`GET /posts` に移行記事（source=migrated）が公開表示される
- **期待**: 冪等（再実行で重複0）、published 表示

### S3: U1 フロント → U3 API（E2E手前の結合）
- **セットアップ**: `iyf-public-web/.env` に `VITE_API_BASE_URL=<U3のURL>`、`npm run dev`
- **手順**: トップ/ブログ/お知らせ/カレンダーが実データ表示、問い合わせ送信が成功
- **期待**: CORS 許可（U3にCloudFront/localhostオリジン設定）、正常表示・送信

### S4: U5 配信 ↔ U1 成果物
- **手順**: `npm run build` → `aws s3 sync dist/ s3://<WebBucketName>/` → CloudFront URL でサイト表示
- **期待**: セキュリティヘッダ（CSP/HSTS等）付与、ディープリンク（/blog/:id直アクセス）が index にフォールバック

## 実行環境の起動例
```bash
# backend をローカルAPIで
cd iyf-backend-api && sam local start-api   # Docker 必要
# frontend
cd iyf-public-web && VITE_API_BASE_URL=http://127.0.0.1:3000 npm run dev
```

## 注記
- 厳密なCI統合スイートは未同梱（小規模・低コスト方針）。上記は手動/半自動の結合確認手順。
- CORS 許可オリジンは U3 の `ALLOWED_ORIGINS` に設定（ローカルは `http://localhost:5173`）。
