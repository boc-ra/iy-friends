# Performance Test Instructions — IYフレンズ Phase 1（軽量）

## 位置づけ
小規模（月 数千〜1万PV, NFR-PERF-01）・低コスト最優先・厳密なSLAなし（Q-N2=A）。
本格的な負荷試験は不要。**軽量な健全性確認**のみ実施する。

## パフォーマンス目安（SLAではない）
- 公開読み取りAPI: 通常時 概ね1秒以内（p50目安）
- CloudFront キャッシュヒット時はさらに高速

## 軽量チェック手順
### 1. API 応答の簡易計測
```bash
# 数回叩いて体感・時間を確認（例）
curl -w "time_total=%{time_total}\n" -o /dev/null -s "<API>/posts"
```
- 期待: キャッシュ/軽量クエリで概ね1秒以内。極端な遅延がないこと。

### 2. フロント配信（CloudFront）
- ブラウザ DevTools の Network で初回/再訪の読み込みを確認（キャッシュ効果）。
- 画像除外・ペイロード最小化により軽量。

### 3. （任意）簡易負荷
```bash
# k6 等がある場合の最小例（低VUで十分）
# k6 run --vus 5 --duration 30s script.js
```

## 最適化の指針（必要時のみ）
- DynamoDB は Query/GetItem 中心・Scan回避（実装済み）
- API Gateway / CloudFront キャッシュ活用（実装/設計済み）
- プロビジョンド同時実行やDAXは**コストのため不採用**（現状の規模では不要）

## 判定
- 体感で明らかな遅延がなければ Phase 1 は合格とする（厳密SLAなし）。
