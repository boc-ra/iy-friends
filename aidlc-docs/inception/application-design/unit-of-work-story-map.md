# ストーリー→ユニット マッピング (Unit of Work Story Map) — IYフレンズ公式サイト

全ユーザーストーリー（US-01〜US-19）をユニットへ割り当てる。
複数ユニットにまたがるストーリー（フロント＋バックエンド）は主担当と関与ユニットを示す。

---

## マッピング表

| ストーリー | 概要 | 主ユニット | 関与ユニット | Phase | 優先度 |
|---|---|---|---|:--:|:--:|
| US-01 | トップ最新情報 | U1 | U3(content) | 1 | Must |
| US-02 | 紹介/沿革 | U1 | — | 1 | Must |
| US-03 | 規約 | U1 | — | 1 | Must |
| US-04 | ブログ一覧/アーカイブ | U1 | U3(content) | 1 | Must |
| US-05 | ブログ詳細 | U1 | U3(content) | 1 | Must |
| US-06 | 既存ブログ移行閲覧 | U4 | U3(content), U1 | 1 | Must |
| US-07 | ブログ投稿 | U2 | U3(content), U3(auth) | 2 | Must |
| US-08 | お知らせ閲覧 | U1 | U3(content) | 1 | Must |
| US-09 | お知らせ投稿 | U2 | U3(content), U3(auth) | 2 | Must |
| US-10 | カレンダー閲覧 | U1 | U3(calendar) | 1 | Should |
| US-11 | カレンダー登録 | U2 | U3(calendar), U3(auth) | 2 | Should |
| US-12 | 募集案内 | U1 | — | 1 | Should |
| US-13 | 問い合わせ送信 | U1 | U3(contact), U5(SES) | 1 | Must |
| US-14 | 問い合わせ管理 | U2 | U3(contact), U3(auth) | 2 | Must |
| US-15 | ログイン | U2 | U3(auth), U5(Cognito) | 2 | Must |
| US-16 | 編集者招待 | U2 | U3(auth), U5(Cognito) | 2 | Must |
| US-17 | レスポンシブ/UX | U1 | U2 | 1 | Must |
| US-18 | セキュリティ（横断） | U5 | U1,U2,U3 | 1&2 | Must |
| US-19 | 低コスト運用（横断） | U5 | U3 | 1&2 | Should |

---

## ユニット別ストーリー集計

### U1 public-web（Phase 1）
US-01, 02, 03, 04, 05, 08, 10, 12, 13, 17（主）／ US-06, 18 に関与

### U2 admin-web（Phase 2）
US-07, 09, 11, 14, 15, 16（主）／ US-17, 18 に関与

### U3 backend-api（Phase 1&2）
公開読取: US-01,04,05,08,10（content/calendar）／ 送信: US-13（contact）
管理: US-07,09,11,14（content/calendar/contact）／ 認証認可: US-15,16（auth）
横断: US-18,19

### U4 blog-migration（Phase 1）
US-06（主）

### U5 infra（Phase 1&2）
US-18（セキュリティ・主）, US-19（低コスト・主）／ US-13(SES), US-15/16(Cognito) の基盤提供

---

## 検証
- [x] 全19ストーリーがユニットに割当済み（漏れなし）
- [x] スコープ外（WN-01〜05）はユニット割当対象外（掲示板/会員/氏名公開/写真/カウンタ）
- [x] Phase 1/2 とユニットの整合を確認
- [x] 横断ストーリー（US-18/19）は infra 主担当＋各ユニット関与として明示
