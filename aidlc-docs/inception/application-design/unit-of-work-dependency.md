# ユニット依存関係 (Unit of Work Dependency) — IYフレンズ公式サイト

ユニット間の依存関係・構築順序を示す。

---

## 依存マトリクス
「行 → 列」= 行が列に依存する。

| ↓依存元 / 依存先→ | U1 public-web | U2 admin-web | U3 backend-api | U4 blog-migration | U5 infra |
|---|:--:|:--:|:--:|:--:|:--:|
| U1 public-web | — | | ●(PublicApi) | | ●(配信基盤) |
| U2 admin-web | | — | ●(AdminApi/認証) | | ●(配信基盤) |
| U3 backend-api | | | — | | ●(APIGW/DDB/Cognito/SES) |
| U4 blog-migration | | | ●(content投入) | — | (実行環境) |
| U5 infra | | | | | — |

- **U5 infra** は他ユニットが動く土台（APIGW/Lambda/DynamoDB/Cognito/SES/配信）を提供 → 依存の起点
- **U3 backend-api** は U1/U2 が消費するAPIを提供
- **U4** は U3(content) を通じてデータ投入
- ユニット間はAPI契約（PublicApi/AdminApi）で疎結合。**循環依存なし**

## 構築・デプロイ順序

### Phase 1（公開サイト）
```
1. U5 infra（公開系: S3/CloudFront/PublicApiGW/Lambda/DynamoDB/SES）
2. U3 backend-api（公開読取＋問い合わせ送信モジュール: content/calendar/contact + common）
3. U4 blog-migration（既存記事の投入）
4. U1 public-web（SSGビルド → S3/CloudFront配信）
```

### Phase 2（管理CMS）
```
5. U5 infra（追加: Cognito, AdminApiGW, 管理系権限/監視強化）
6. U3 backend-api（管理モジュール: auth + content/calendar/contact の管理API）
7. U2 admin-web（認証SPA → 配信）
```

## クリティカルパス
- **U5 infra → U3 backend-api → (U4, U1)**（Phase 1）
- **U5 infra(認証) → U3(auth+管理API) → U2 admin-web**（Phase 2）

## 調整ポイント（Coordination）
- **API契約**: PublicApi/AdminApi のスキーマは U3 が定義し、U1/U2 が追従（契約変更時は両者同期）
- **認証契約**: Cognito のプール/クライアント設定（U5）を U2/U3 が参照
- **データ契約**: DynamoDB スキーマ（Functional Design で確定）を U3/U4 が共有

## テスト・ロールバック方針
- **テスト**: ユニット単位（unit + PBT部分適用）→ Phase単位で結合テスト（Build and Test 段階）
- **ロールバック**: 新規サイトのため容易。Phase 1 を先行公開し、Phase 2 は準備完了後に有効化（段階リリースでリスク低減）
