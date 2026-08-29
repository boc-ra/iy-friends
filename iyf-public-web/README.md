# iyf-public-web（IYフレンズ 公開サイト / U1）

サッカークラブ「IYフレンズ」の公開フロント。**Vite + React + TypeScript**、apple-design 原則、レスポンシブ。
U3 の公開APIを消費し、U5 の S3/CloudFront へ配信する。

## ローカルで画面確認（API不要）
```bash
npm install
npm run dev
# → http://localhost:5173 をブラウザで開く
```
`VITE_API_BASE_URL` を設定していない場合は**ダミーデータ**で表示されます（画面上部にデモ帯）。
実APIに繋ぐときは `.env` を作成:
```
VITE_API_BASE_URL=https://xxxx.execute-api.ap-northeast-1.amazonaws.com/prod
```

## ページ
`/`（トップ）`/blog`・`/blog/:id`・`/notices`・`/calendar`・`/about`・`/join`・`/terms`・`/contact`

## ビルド / デプロイ
```bash
npm run build          # dist/ に静的ファイル
# U5 の S3 バケットへ同期し、CloudFront を無効化
aws s3 sync dist/ s3://<WebBucketName>/ --delete
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```

## デザイン方針（apple-design）
- システムフォント優先（光学サイズ内蔵）、見出しは負トラッキング＋締めたleading、本文は緩め
- 半透明ヘッダ（`backdrop-filter`）、大きい面ほど厚い影で奥行き
- 抑制した動き（短い fade、押下で即時 scale フィードバック）
- `prefers-reduced-motion` / `prefers-reduced-transparency` / `prefers-contrast` / ダークモード対応
- 全インタラクティブ要素に `data-testid`（自動化フレンドリー）

## 構成
```
src/
  api/       client.ts(型・ダミーfallback) / types.ts / dummy.ts
  components/ Layout / Header / Footer / States
  hooks/     useAsync.ts
  lib/       format.ts(JST日付)
  pages/     Home/BlogList/BlogDetail/Notices/Calendar/About/Join/Terms/Contact/NotFound
  styles/    tokens.css / global.css / components.css
```

## 注意
- 静的テキスト（紹介/沿革/規約/入会費用）はサンプル。実内容に差し替えてください。
- SPA のため CloudFront で 403/404 を `index.html` に返す設定（U5 テンプレート済）。
