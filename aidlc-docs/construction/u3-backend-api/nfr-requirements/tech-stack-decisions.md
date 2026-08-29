# Tech Stack Decisions — U3 backend-api（IYフレンズ）

要件定義で技術スタックは確定済み（CON-02: バックエンド Python 確定）。本書は U3 backend-api の実装技術を確定し、NFR 回答（低コスト最優先）を反映した選定理由を記録する。

---

## 1. 確定スタック

| 層 | 技術 | 状態 | 根拠 |
|---|---|---|---|
| 言語/ランタイム | **Python 3.13**（AWS Lambda） | 確定 | CON-02。サーバーレス従量課金（NFR-COST-01） |
| API 実行 | **AWS Lambda** | 確定 | 小規模・従量課金・運用負荷最小（NFR-OPS-01） |
| API 公開 | **Amazon API Gateway（HTTP API）** | 確定（Infra Designで最終化） | REST API より低コスト・低レイテンシ。スロットリング（SECURITY-11） |
| データストア | **Amazon DynamoDB（On-Demand）** | 確定 | サーバーレス・従量・自動スケール。小規模で最安（NFR-U3-SCALE-01） |
| 認証 | **Amazon Cognito** | 確定 | 管理者/編集者認証、MFA、ブルートフォース対策（SECURITY-12） |
| メール通知 | **Amazon SES** | 確定 | 問い合わせ受付通知。低コスト |
| 秘密情報 | **AWS Secrets Manager**（または SSM Parameter Store SecureString） | 確定（Infraで最終化） | 平文保管禁止（SECURITY-12）。コスト観点で最小構成を Infra Design で確定 |
| リージョン | **ap-northeast-1（東京）単一** | 確定 | JST運用、低遅延、単一リージョン（Q-N3=A / NFR-U3-AVAIL-01） |

## 2. アプリケーション構成（U3 内部）

- **アーキテクチャ**: モジュラモノリス（1つのデプロイ単位／論理モジュール分割）
  - `content`（ブログ・お知らせ = Post/Notice）
  - `calendar`（イベント = Event）
  - `contact`（問い合わせ = Inquiry、SES通知）
  - `common`（認証/認可・バリデーション・ロギング・エラーハンドリング・DynamoDBアクセス）
- **根拠**: 小規模で複数マイクロサービスは過剰（運用・コスト増）。関心分離は論理モジュールで達成（NFR-U3-MNT-01）。

## 3. ライブラリ選定（方針）

| 用途 | 候補 | 方針 |
|---|---|---|
| 入力検証 | **Pydantic v2** | SECURITY-05（型・長さ・形式のスキーマ検証）。Code Generation で確定 |
| DynamoDB アクセス | **boto3**（低レベル）＋薄いリポジトリ層 | パラメータ化アクセス、Scan回避。ORM は導入しない（軽量・低コスト） |
| ロギング | 標準 `logging` + 構造化（JSON）・相関ID | SECURITY-03。PII非出力 |
| テスト | pytest ＋ **Hypothesis（PBT 部分適用）** | 純粋関数・シリアライズ往復のみ（PBT方針に準拠） |
| 依存管理 | ロックファイル（例: `requirements.txt` ハッシュ固定 / `uv` / `poetry.lock`） | SECURITY-10（バージョン固定・脆弱性スキャン）。Code Generation で確定 |

## 4. NFR 回答が選定に与えた影響

| 回答 | 技術選定への反映 |
|---|---|
| Q-N1=A（PITR） | DynamoDB PITR 有効化。追加のバックアップ自動化基盤は導入しない（コスト） |
| Q-N2=A（1秒目安・SLAなし） | プロビジョンド同時実行なし、キャッシュ（API Gateway/CloudFront）活用。過剰な性能投資をしない |
| Q-N3=A（単一リージョン） | マルチリージョン用の複製・フェイルオーバー基盤を導入しない |

## 5. 明示的に採用しないもの（コスト最適化）

- プロビジョンド同時実行 / DynamoDB プロビジョンドキャパシティ
- マルチリージョン複製・グローバルテーブル
- 常時稼働のコンテナ/EC2/RDS（サーバーレスで代替）
- 追加のスケジュールバックアップ基盤（PITR で代替）

## 6. 後段への申し送り（Infrastructure Design）

- API Gateway（HTTP API vs REST API）の最終確定とスロットリング値
- Secrets Manager vs SSM Parameter Store のコスト比較・確定
- CloudWatch アラーム/ダッシュボード、ログ保持90日設定（SECURITY-14）
- IAM 最小権限ポリシーの具体定義（SECURITY-06）
- S3/CloudFront（U1/U5側）連携点
