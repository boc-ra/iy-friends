# ユニット分解 計画 (Unit of Work Plan) — IYフレンズ公式サイト

このファイルは Units Generation ステージの **Part 1（計画）** です。
下部の **確認質問** に回答（`[Answer]:` タグ）いただいた後、承認をもって Part 2（ユニット成果物生成）へ進みます。

---

## 1. 目的
アプリケーション設計（`application-design/`）を、開発・デプロイの単位（Unit of Work）へ分解する。
2段階リリース（Phase 1 公開サイト / Phase 2 管理CMS）に整合させる。

## 2. ユニット初期案（回答後に確定）
| 候補ユニット | 種別 | 内容 | Phase |
|---|---|---|---|
| U1 public-web | Frontend(Service) | 公開サイト（SSG）＝PublicWebApp | 1 |
| U2 admin-web | Frontend(Service) | 管理CMS（認証SPA）＝AdminWebApp | 2 |
| U3 backend-api | Backend(Service) | Content/Calendar/Contact/Auth を内包（モジュール分割） | 1&2 |
| U4 blog-migration | Batch | 既存記事のスクレイピング移行ツール | 1 |
| U5 infra | IaC | CDK（S3/CloudFront/APIGW/Lambda/DynamoDB/Cognito/SES/監視） | 1&2 |

## 3. 生成する成果物（Part 2）
- [x] `unit-of-work.md`（ユニット定義・責務・コード配置戦略）
- [x] `unit-of-work-dependency.md`（ユニット依存マトリクス）
- [x] `unit-of-work-story-map.md`（ストーリー→ユニットの割当）

---

# 確認質問（回答をお願いします）

各 `[Answer]:` に記号（A, B, C ...）を記入してください。合う選択肢がなければ `X) Other` を選び自由記述してください。すべて回答したら「完了」とお知らせください。

## Q-U1: バックエンドの分解粒度
バックエンド（Content/Calendar/Contact/Auth）をどう分割しますか？（コスト・運用に影響）

A) 1つのバックエンドサービスに統合し、内部を論理モジュールに分ける（モジュラーモノリス）。小規模・低コスト・運用が楽（AI推奨）

B) サービスごとに独立デプロイ（マイクロサービス）。分離度は高いが運用/コスト増

X) Other（自由記述）

[Answer]: A

## Q-U2: フロントの分解（公開/管理）
公開サイトと管理CMSのユニット分けは？（Q-A2=A 別アプリ分離を反映）

A) 公開(U1)と管理(U2)を別ユニットに分ける（AI推奨・Phase分割と一致）

B) 1つのフロントユニットにまとめる

X) Other（自由記述）

[Answer]: A

## Q-U3: 開発・リリースの進め方
ユニットの実装順序の方針は？

A) Phase 1（U1 public-web / U3 backend-api の公開分 / U4 移行 / U5 infra）を先に完成させ、その後 Phase 2（U2 admin-web / U3 の管理分・認証）（AI推奨）

B) 全ユニットを並行して進める

C) おまかせ

X) Other（自由記述）

[Answer]: A

## Q-U4: 移行ツールの位置づけ
ブログ移行ツール（U4）は独立ユニットにしますか？

A) 独立の移行ユニットにする（一度きり〜再実行のバッチとして明確化）（AI推奨）

B) backend-api の一部に含める

X) Other（自由記述）

[Answer]: A
