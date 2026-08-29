# Code Generation Summary — U1 public-web（Phase 1）

生成場所: ワークスペース直下 `iyf-public-web/`（Vite + React + TypeScript）。apple-design skill 適用。

## 回答（推奨・全A）
Q-P1=A（Vite+React+TS SPA）/ Q-P2=A（素のCSS+CSS Modules）/ Q-P3=A（全ページ）/ Q-P4=A（ダミーデータでローカル確認可）。

## 生成ファイル（主要）
- 設定: `package.json` `tsconfig.json` `vite.config.ts` `index.html` `.env.example` `.gitignore` `README.md` `src/vite-env.d.ts`
- スタイル（apple-design）: `src/styles/tokens.css` `global.css` `components.css`
- API: `src/api/{client,types,dummy}.ts`（U3契約の型・ダミーfallback）
- 部品: `src/components/{Layout,Header,Footer,States}.tsx`、`src/hooks/useAsync.ts`、`src/lib/format.ts`
- ページ（9＋404）: `Home` `BlogList` `BlogDetail` `Notices` `Calendar` `About` `Join` `Terms` `Contact` `NotFound`
- ルーティング: `src/App.tsx` `src/main.tsx`

## ストーリー対応
US-01（トップ最新）/ US-04（ブログ一覧）/ US-05（詳細）/ US-08（お知らせ）/ US-10（カレンダー）/ US-02（紹介・沿革）/ US-03（規約）/ US-12（募集）/ US-13（問い合わせ）/ US-17（レスポンシブ・UX横断）。

## apple-design の反映
- システムフォント優先・見出しは負トラッキング＋締めたleading・本文は緩め
- 半透明ヘッダ（backdrop-filter）、大きい面ほど厚い影、押下で即時 scale フィードバック、短い fade 入場
- `prefers-reduced-motion` / `prefers-reduced-transparency` / `prefers-contrast` / ダークモード対応
- 全インタラクティブ要素に `data-testid`（自動化フレンドリー）

## API連携 / ローカル確認（Q-P4=A）
- `VITE_API_BASE_URL` 未設定 → ダミーデータで表示（デモ帯を表示）。`npm run dev` で即画面確認。
- 設定時は U3 の `/posts` `/notices` `/events` `/contact` を呼び出し。

## 検証状況
- 相対import整合チェック: **PASS**（全参照が実ファイルに対応）。
- 型チェック/ビルド（`npm run build`）: **本環境に Node 未導入のため未実行** → Build & Test フェーズ／利用者環境で実施予定。

## セキュリティ/UX
- 問い合わせはクライアント検証＋二重送信防止（送信中ボタン無効化）、本検証はU3。
- 配信時セキュリティヘッダは U5 CloudFront（SECURITY-04）。外部スクリプトは原則自己ホスト（SECURITY-13）。

## デプロイ
`npm run build` → `dist/` を U5 の S3（`WebBucketName`）へ同期 → CloudFront 無効化。
