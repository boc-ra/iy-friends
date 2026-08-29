# NFR Requirements — U3 backend-api（IYフレンズ）

対象ユニット: **U3 backend-api**（モジュラモノリス: content / calendar / contact / common。Phase 1）
前提: 小規模・低コスト最優先・Python サーバーレス。Security Baseline 全適用（ブロッキング）。PBT 部分適用。
本書は要件定義（`aidlc-docs/inception/requirements/requirements.md`）の確定 NFR を U3 に落とし込み、NFR プランの回答（Q-N1/Q-N2/Q-N3 = すべて A＝最低コスト）を反映したもの。

---

## 1. 意思決定サマリ（本ステージの回答）

| ID | テーマ | 決定 | 根拠 |
|---|---|---|---|
| Q-N1 | データバックアップ | **DynamoDB PITR（最大35日）を有効化** | 「安いほう」指示。小規模データではPITRが日次スナップショット自動化より安く・簡単・安全。NFR-OPS-02 / DR-06 を満たす |
| Q-N2 | API 応答目標 | **通常時 概ね1秒以内を設計目標（厳密SLAなし）** | 「安いほう」指示。速度目標引き上げはコスト増。NFR-PERF-01/02 と整合 |
| Q-N3 | 可用性 | **単一リージョンのマネージド構成**（厳密なRTO/RPO目標なし） | 「安いほう」指示。マルチリージョンはコスト増。小規模クラブサイトに過剰 |

---

## 2. 性能（Performance）

| NFR-ID | 要件 | U3 での具体化 |
|---|---|---|
| NFR-PERF-01 | 想定規模は小規模（月 数千〜1万PV） | Lambda 同時実行は既定枠で十分。プロビジョンド同時実行は使わない（コスト） |
| NFR-PERF-02 | CDN で静的配信 | 公開GET系（記事・お知らせ・イベント一覧/詳細）は CloudFront + API Gateway キャッシュ活用を前提に設計 |
| **NFR-U3-PERF-01** | 公開読み取りAPIは通常時 概ね1秒以内（p50目安、SLAではない） | ページング10件（Q-F6）、DynamoDB は Query/GetItem 中心・Scan回避、必要に応じ GSI |
| **NFR-U3-PERF-02** | 書き込み（問い合わせ送信・投稿）は同期処理で数秒以内 | SES送信はベストエフォート。失敗時もDB保存は成立（後述 SECURITY-15 fail-closed と両立） |

## 3. スケーラビリティ（Scalability）

| NFR-ID | 要件 | U3 での具体化 |
|---|---|---|
| NFR-U3-SCALE-01 | 従量課金でアクセス変動に自動追従 | Lambda + DynamoDB **On-Demand キャパシティ**（小規模で最安・自動スケール） |
| NFR-U3-SCALE-02 | 明示的なスケーリング閾値・キャパシティ計画は設けない | 小規模前提。急増は現時点で非対象（将来 CloudWatch で監視のみ） |

## 4. 可用性・信頼性（Availability / Reliability）

| NFR-ID | 要件 | U3 での具体化 |
|---|---|---|
| NFR-U3-AVAIL-01 | 単一リージョン（東京 ap-northeast-1）のマネージド構成 | マルチAZは各マネージドサービスが内包。マルチリージョンは非対象 |
| NFR-U3-AVAIL-02 | 厳密な RTO/RPO 目標は設けない | 復旧目標はベストエフォート。PITR により最大35日前まで復元可能（RPO実質数分〜） |
| NFR-U3-REL-01 | 全外部呼び出しにエラーハンドリング・fail-closed | SECURITY-15 準拠。DynamoDB/SES/Cognito 呼び出しは try/except、認可・検証は失敗時に拒否 |
| NFR-U3-REL-02 | グローバル例外ハンドラで安全応答 | 未捕捉例外は汎用エラー（詳細非表示）で 5xx、構造化ログに記録 |

## 5. バックアップ・データ保護（Backup / Data Protection）

| NFR-ID | 要件 | U3 での具体化 |
|---|---|---|
| NFR-U3-BAK-01 | DynamoDB **PITR 有効化**（継続バックアップ、最大35日） | Q-N1=A。誤削除・破損から復旧。子供/保護者の問い合わせPIIを扱うため重要 |
| NFR-U3-BAK-02 | 保存時・転送時暗号化 | SECURITY-01。DynamoDB は AWS 管理キーで保存時暗号化、全通信 TLS1.2+ |
| NFR-U3-BAK-03 | PII 最小化・保持方針 | 問い合わせは name/email/message（Q-F3）。ログにPIIを出さない（SECURITY-03） |

## 6. セキュリティ（Security）※ Security Baseline 全適用・ブロッキング

U3（バックエンドAPI）で本ステージ適用・確約する項目（インフラ層は Infrastructure Design で担保）:

| SECURITY-ID | U3 での NFR 要件 |
|---|---|
| SECURITY-01 | DynamoDB 保存時暗号化、API/内部通信 TLS1.2+ 強制 |
| SECURITY-03 | Lambda 構造化ロギング（相関ID付）。PII・秘密情報をログ出力しない |
| SECURITY-05 | 全 API 入力をスキーマ検証（型・長さ・形式・サニタイズ・パラメータ化アクセス） |
| SECURITY-06 | Lambda 実行ロールは最小権限（対象テーブル/操作を限定、ワイルドカード禁止、読み書き分離） |
| SECURITY-08 | 管理系は認証必須＋サーバー側ロール検証、オブジェクトレベル認可（IDOR防止）、CORS はオリジン限定 |
| SECURITY-11 | 認証・認可ロジックを common モジュールに集約。公開エンドポイントにレート制限（API Gateway スロットリング） |
| SECURITY-12 | Cognito 認証、秘密情報は Secrets Manager、管理者 MFA、ブルートフォース対策（Cognito 機能） |
| SECURITY-13 | 重要データ変更（投稿・問い合わせ状態遷移）は監査可能（actor/timestamp/before-after をログ） |
| SECURITY-14 | 認証失敗・認可違反のアラート、ログ保持 90日以上、アプリは自ログを削除不可 |
| SECURITY-15 | 全外部呼び出しにエラーハンドリング、fail-closed、汎用エラーメッセージ、グローバルエラーハンドラ |

> インフラ寄りの SECURITY-02（アクセスログ）/04（HTTPヘッダ、U1側HTML配信）/07（ネットワーク）/09（ハードニング・S3公開ブロック）/10（依存固定・脆弱性スキャン）は **Infrastructure Design / Code Generation で担保**（本ステージでは要件として明記、成果物レベルの検証は後段）。

## 7. 保守性・運用（Maintainability / Operability）

| NFR-ID | 要件 |
|---|---|
| NFR-OPS-01 | マネージドサービス中心で運用負荷最小化 |
| NFR-OPS-03 | 監視・ログ最低限（CloudWatch Logs + 主要メトリクスのアラーム、SECURITY-14 準拠） |
| NFR-U3-MNT-01 | モジュラモノリス（content/calendar/contact/common）で関心分離。共通ロジックは common に集約 |
| NFR-U3-MNT-02 | PBT 部分適用：純粋関数・シリアライズ往復（API⇔DynamoDBモデル変換、日付/カテゴリ整形）にプロパティテスト |

## 8. コスト（Cost）

| NFR-ID | 要件 |
|---|---|
| NFR-COST-01 | 運用コスト極小（目安 月 数百円規模）。サーバーレス従量課金 |
| NFR-U3-COST-01 | DynamoDB On-Demand、Lambda 従量、プロビジョンド同時実行なし、単一リージョン、PITR のみ（追加スナップショット自動化なし） |

---

## 9. 未解決事項・後段への申し送り

- SECURITY-02/04/07/09/10 の成果物レベル検証 → Infrastructure Design / Code Generation
- 監視ダッシュボード/アラーム定義の具体化 → Infrastructure Design
- 独自ドメイン追加（NFR-DOM-02）は Phase 1 では非対象（デフォルトドメインで公開）

## 10. トレーサビリティ

- 参照要件: NFR-PERF-01/02, NFR-COST-01, NFR-OPS-01/02/03, DR-06, SECURITY-01/03/05/06/08/11/12/13/14/15
- 参照機能設計: `../functional-design/domain-entities.md`, `business-logic-model.md`, `business-rules.md`
- 反映した回答: Q-N1=A, Q-N2=A, Q-N3=A（`../../plans/u3-backend-api-nfr-requirements-plan.md`）
