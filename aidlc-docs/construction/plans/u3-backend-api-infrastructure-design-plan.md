# Infrastructure Design 計画 — U3 backend-api（IYフレンズ）

NFR設計（`../u3-backend-api/nfr-design/`）で論理構成は確定。ここでは論理コンポーネントを AWS 物理リソースに対応付ける。
リージョンは東京（ap-northeast-1）単一、低コストサーバーレスが前提。実質的な選択が残る点のみ確認する。

> 補足: 共有インフラ（S3/CloudFront/Cognito 等）は後続の **U5 infra ユニット**で最終集約する。U3 では backend-api 側の論理→物理対応を確定し、U5 へ申し送る。

---

## 確定済み（再確認不要）
- リージョン: ap-northeast-1（東京）単一
- 実行: Lambda（Python 3.13）／公開: API Gateway（HTTP API, スロットリング, キャッシュ）
- データ: DynamoDB On-Demand（PITR, 保存時暗号化）
- 認証: Cognito ／ 通知: SES ／ ログ: CloudWatch Logs（保持90日）
- 不採用: SQS / DAX / プロビジョンド同時実行 / マルチリージョン

## 生成する成果物（回答後）
- [x] `infrastructure-design.md`
- [x] `deployment-architecture.md`
- [x] `shared-infrastructure.md`（U5への申し送りメモとして）

## 回答（「A」により全てA採用）
- Q-I1 = A（AWS SAM）
- Q-I2 = A（マルチテーブル）
- Q-I3 = A（SSM Parameter Store SecureString）
- Q-I4 = A（本番のみで開始）

---

# 確認質問（回答をお願いします）

各質問とも **AI推奨はすべて最安・シンプル路線（A）**。「**推奨で**」で一括Aにできます。

## Q-I1: IaC（インフラ定義）ツール
インフラをコード化するツールは？

A) **AWS SAM**（サーバーレス特化・記述最小・無料。Lambda/API GW/DynamoDB に最適）（AI推奨）

B) AWS CDK（Python）— プログラマブルだが学習・記述量やや多い

C) Terraform — マルチクラウド向け。今回はオーバースペック

D) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-I2: DynamoDB テーブル設計
データの持ち方は？

A) **マルチテーブル**（Post / Notice / Event / Inquiry / User をテーブル分割）。分かりやすく、On-Demand なのでコスト差はほぼ無し（AI推奨）

B) シングルテーブル設計（1テーブルに集約）— DynamoDB流儀だが設計・保守が複雑

C) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-I3: 秘密情報の保管先
SES等の秘密情報・設定値の保管は？

A) **SSM Parameter Store（SecureString）**（実質無料で最安。小規模に十分）（AI推奨）

B) Secrets Manager（自動ローテーション等が強力だが 1シークレット月 約$0.4 のコスト）

C) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-I4: 環境（ステージ）構成
デプロイ環境をどう分けるか？

A) **本番（prod）のみで開始**（最小コスト。サーバーレスは従量なので後から dev を追加しても安価）（AI推奨）

B) dev + prod の2環境を最初から用意

C) おまかせ

X) Other（自由記述）

[Answer]: 
