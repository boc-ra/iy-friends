# Infrastructure Design 計画 — U5 infra（IYフレンズ）

U5 は共有インフラ（S3/CloudFront/Cognito/ドメイン/監視）と、Security Baseline のインフラ担保を確定・IaC化するユニット。
U3 の申し送り（`../shared-infrastructure.md`）を受けて、残る実質的な選択を確認する。

> 前提（確定済み）: 単一リージョン東京、低コストサーバーレス、Security Baseline 全適用。
> U3 backend は既に SAM（`iyf-backend-api/template.yaml`）で構築済み・24テスト通過。

## 生成する成果物（回答後）
- [x] `infrastructure-design.md`（U5：共有インフラの論理→物理）
- [x] `deployment-architecture.md`（U5：スタック構成・デプロイ・連携）

## 回答（「推奨で」により全てA採用）
- Q-U1 = A（SAM統一・U5は共有インフラのみ。U3再作業なし。※Inception時のCDK案はSAMへ変更＝ツール統一のため）
- Q-U2 = A（CloudFrontデフォルトドメインで開始、独自ドメインは後付け）
- Q-U3 = A（標準の制限的セキュリティヘッダを自動付与）
- Q-U4 = A（最小監視＋ログ90日）
- Q-U5 = A（Phase 1でCognito作成、U3が参照、MFA・パスワードポリシー）

---

# 確認質問（回答をお願いします）

各質問とも **AI推奨はすべて最安・シンプル・整合性重視（A）**。「**推奨で**」で一括Aにできます。

## Q-U1: IaC ツールと U5 の担当範囲（最重要の調整点）
U3 は SAM で構築済み。U5 の共有インフラをどう扱うか？

A) **U3 と同じ SAM に統一し、U5 は「共有インフラのみ」を別 SAM スタックで定義**（S3/CloudFront/Cognito/監視/ドメイン）。ツール統一・学習コスト最小・U3 の再作業なし（AI推奨）

B) 当初案どおり **CDK** で共有インフラを定義（SAM と CDK の2ツール併用になる）

C) CDK で **全インフラを統合**（U3 の SAM も CDK へ移行＝再作業が発生）

D) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-U2: 公開ドメイン
Phase 1 の公開URLは？

A) **CloudFront デフォルトドメイン（`*.cloudfront.net`）で開始**（費用0円、NFR-DOM-01）。独自ドメインは後から追加できる構成にする（AI推奨）

B) 最初から独自ドメイン（`iy-o-endan.com` 引き継ぎ or 新規取得）＋ACM証明書を設定

C) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-U3: CloudFront のセキュリティヘッダ（SECURITY-04）
HTML配信時のセキュリティヘッダ（CSP/HSTS 等）は？

A) **標準の制限的ポリシーを CloudFront Response Headers Policy で自動付与**（CSP=default-src 'self' 基準、HSTS 1年、X-Content-Type-Options 等）（AI推奨）

B) CSP を細かくカスタム定義したい（許可オリジン等を個別指定）

C) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-U4: 監視・アラートの範囲（SECURITY-14 / NFR-OPS-03）
どこまで監視するか？

A) **最小構成**：Lambda エラー率・API 5xx・認証失敗のアラート＋ログ保持90日（AI推奨・低コスト）

B) 詳細ダッシュボード（レイテンシ/コスト/各種メトリクスの可視化）も用意

C) おまかせ

X) Other（自由記述）

[Answer]: 

## Q-U5: Cognito（管理者・編集者認証）の作成タイミング
Phase 2 で使う Cognito をいつ作るか？

A) **U5（Phase 1）で User Pool を作成しておき、U3 は参照（Import）**。Phase 2 の認証実装がスムーズ。MFA（管理者必須）・パスワードポリシーもここで設定（AI推奨）

B) Phase 2 に入ってから作成（Phase 1 では作らない）

C) おまかせ

X) Other（自由記述）

[Answer]: 
