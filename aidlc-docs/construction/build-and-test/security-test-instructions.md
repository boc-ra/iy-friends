# Security Test Instructions — IYフレンズ Phase 1

Security Baseline（ブロッキング）適用プロジェクト。Phase 1 で検証すべき項目。

## 1. 依存の脆弱性スキャン（SECURITY-10）
```bash
# backend
cd iyf-backend-api && pip install pip-audit && pip-audit -r requirements.txt
# frontend
cd iyf-public-web && npm audit --production
```
- 期待: 既知の重大脆弱性なし。CI（`.github/workflows/ci.yml`）でも自動実行。

## 2. 入力検証（SECURITY-05）
- `POST /contact` に不正入力（型違い/超過長/欠落/HTML）を送り、400 と汎用メッセージを確認。
- スクリプト混入（`<script>`）が保存前にサニタイズされること（`test_contact.py` で確認済み）。

## 3. 認可・存在秘匿（SECURITY-08）
- draft 記事の詳細取得が 404（存在秘匿）であること（`test_content.py` で確認済み）。
- 公開エンドポイントのみ Phase 1 で開放。管理系は Phase 2（Cognito）。

## 4. 配信ヘッダ（SECURITY-04）
- CloudFront 経由の HTML 応答に CSP/HSTS/X-Content-Type-Options/X-Frame-Options/Referrer-Policy が付くこと。
```bash
curl -I https://<cloudfront-domain>/ | grep -iE "content-security|strict-transport|x-content-type|x-frame|referrer"
```

## 5. S3 公開ブロック（SECURITY-09）
- WebBucket が直接アクセス不可（CloudFront OAC 経由のみ）であること。

## 6. ログにPIIが出ない（SECURITY-03）
- 構造化ログに email/message/name が出力されないこと（`mask_pii`、`test_common.py` で確認済み）。

## 7. 最小権限（SECURITY-06）
- Lambda 実行ロールが対象テーブル/操作のみ（`template.yaml` の Policies を確認、ワイルドカードなし）。

## 判定
- 上記すべて満たせば Phase 1 セキュリティ合格。Cognito本認証（SECURITY-12）は Phase 2 で完成。
