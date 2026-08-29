# Code Generation 計画 — U1 public-web（IYフレンズ / Phase 1）

ミニバスケットボールチーム「IYフレンズ」の**公開サイト（フロント）**を生成する。React + TypeScript、apple-design 原則、レスポンシブ。
U3 の公開APIを消費し、U5 の S3/CloudFront へ配信。**この計画がCode Generationの唯一の正**とする。

---

## 1. ユニットコンテキスト
- **配置（ワークスペース直下）**: `iyf-public-web/`
- **ドキュメント**: `aidlc-docs/construction/u1-public-web/code/`
- **消費API**: U3 公開API（`/posts` `/posts/{id}` `/notices` `/notices/{id}` `/events` `/events/{id}` `POST /contact`）
- **デプロイ先**: U5 の `WebBucketName`（S3）→ CloudFront
- **デザイン**: apple-design 原則（余白・タイポグラフィ・素材/奥行き・抑制した動き・アクセシビリティ）。**生成時に apple-design skill を使用**
- **ストーリー**: US-01/02/03/04/05/08/10/12/13/17

## 2. ページ構成（ストーリー由来）
| ページ | ルート | ストーリー |
|---|---|---|
| トップ（最新情報） | `/` | US-01 |
| 紹介・沿革 | `/about` | US-02 |
| 利用規約 | `/terms` | US-03 |
| ブログ一覧 | `/blog` | US-04 |
| ブログ詳細 | `/blog/:id` | US-05 |
| お知らせ | `/notices` | US-08 |
| カレンダー | `/calendar` | US-10 |
| 募集案内 | `/join` | US-12 |
| 問い合わせ | `/contact` | US-13 |
| 横断: レスポンシブ/UX/reduced-motion | 全体 | US-17 |

---

# 確認質問（回答をお願いします）
AI推奨はすべて **A**（最簡・低コスト・すぐローカル確認可）。「**推奨で**」で一括Aにできます。

## Q-P1: フレームワーク/ビルド
A) **Vite + React + TypeScript（SPA）**：最簡・軽量・`npm run dev` で即プレビュー・静的ビルドをS3へ（AI推奨）

B) Next.js（SSG/SEO強いがやや重い）

C) Astro（コンテンツ最適・高速だが学習要）

D) おまかせ

X) Other

[Answer]: 

## Q-P2: スタイリング
A) **素のCSS + CSS Modules**（apple-design原則を自前実装、依存最小・軽量）（AI推奨）

B) Tailwind CSS（ユーティリティ、記法学習あり）

C) UIライブラリ（MUI等、見た目が固定的・重い）

D) おまかせ

X) Other

[Answer]: 

## Q-P3: Phase 1 のページ範囲
A) **上記の全ページを実装**（トップ/紹介/沿革/規約/ブログ/お知らせ/カレンダー/募集/問い合わせ）（AI推奨）

B) 主要ページ（トップ/ブログ/問い合わせ）を先行し、他は後日

C) おまかせ

X) Other

[Answer]: 

## Q-P4: ローカルプレビュー（画面確認）
A) **ダミーデータ同梱で API 未接続でも `npm run dev` で画面確認できる**ようにする（環境変数で実API切替）（AI推奨）

B) 実API接続前提（ローカルは実API必須）

C) おまかせ

X) Other

[Answer]: 

---

## 回答（「推奨で」により全てA採用）
- Q-P1 = A（Vite + React + TypeScript, SPA）
- Q-P2 = A（素のCSS + CSS Modules、apple-design自前実装）
- Q-P3 = A（全ページ実装）
- Q-P4 = A（ダミーデータ同梱で `npm run dev` 即確認、実API切替は環境変数）

## 3. 生成ステップ（回答後・番号順）
### Step 1: プロジェクト構成
- [x] `iyf-public-web/`（Vite+React+TS）、`package.json`、`tsconfig`、`index.html`、`.env.example`（`VITE_API_BASE_URL`）、`.gitignore`

### Step 2: デザイン基盤（apple-design skill 使用）
- [x] `src/styles/`（トークン：余白/タイポグラフィ/カラー、reduced-motion対応、レスポンシブ基盤）
- [x] 共通レイアウト：ヘッダ/ナビ/フッタ、`data-testid` 付与

### Step 3: API クライアント
- [x] `src/api/client.ts`（U3 API 呼び出し、型定義、エラーハンドリング、ダミーデータfallback）

### Step 4: 共通コンポーネント
- [x] カード/一覧/ページネーション/ローディング/空表示など

### Step 5: ページ実装（US別）
- [x] トップ/紹介/沿革/規約/ブログ一覧・詳細/お知らせ/カレンダー/募集/問い合わせフォーム

### Step 6: ルーティング & アクセシビリティ
- [x] React Router、`prefers-reduced-motion`、フォーカス管理、モバイル対応確認

### Step 7: テスト/検証
- [x] 主要コンポーネントの軽量テスト（任意）＋ 型チェック/ビルド確認

### Step 8: ドキュメント/要約
- [x] `iyf-public-web/README.md`（開発/ビルド/デプロイ、`npm run dev` 手順）
- [x] `aidlc-docs/construction/u1-public-web/code/code-generation-summary.md`

## 4. セキュリティ/UX 適合
- SECURITY-04（配信時ヘッダはU5 CloudFront）/13（外部スクリプトはSRI、原則自己ホスト）
- 入力（問い合わせ）はクライアント検証＋U3側で本検証。二重送信防止（ボタン無効化）
- NFR-UX-01〜04（apple-design/レスポンシブ/親しみやすさ/reduced-motion）

## 5. トレーサビリティ
US-01/02/03/04/05/08/10/12/13/17。API契約: `aidlc-docs/construction/u3-backend-api/code/api-documentation.md`。総ステップ数: 8。
