# ビジネスルール (Business Rules) — U3 backend-api

バリデーション・制約・認可・ポリシーを定義する。ID 付きで後続テストに紐づける。

---

## 認可ルール（Authorization）
| ID | ルール |
|---|---|
| BR-AUTH-01 | すべての管理API（AdminApi）はトークン検証を通過しないと拒否（fail-closed, SECURITY-08/12） |
| BR-AUTH-02 | Editor は「自分が作成した Post/Notice」のみ更新・削除可。Admin は全件可 |
| BR-AUTH-03 | 招待・ユーザー無効化・ユーザー一覧・（将来の全体設定）は Admin ロールのみ |
| BR-AUTH-04 | 管理者は自分自身を無効化できない（ロックアウト防止） |
| BR-AUTH-05 | status=disabled のユーザーは全管理API拒否 |
| BR-AUTH-06 | 公開API（PublicApi）は published データの読取と問い合わせ送信のみ許可 |

## バリデーションルール（Validation, SECURITY-05）
| ID | ルール |
|---|---|
| BR-VAL-01 | Post.title 1..120、bodyRichText 必須・許可タグallowlistでサニタイズ |
| BR-VAL-02 | Notice.title 1..120、bodyRichText 必須・サニタイズ |
| BR-VAL-03 | Event.title 1..80、type ∈ {practice,game,other}、startAt 必須、endAt があれば startAt<=endAt |
| BR-VAL-04 | Inquiry.name 1..60、email はRFC準拠形式・..254、message 1..2000（F3=A） |
| BR-VAL-05 | 文字列は前後空白トリム後に長さ判定。制御文字は除去 |
| BR-VAL-06 | 全ての外部入力は型・長さ・形式を検証し、不正は 400（詳細はログのみ） |
| BR-VAL-07 | ページング pageSize 既定=10（F6=A）、上限=50（過大要求の抑制） |

## 状態・ライフサイクルルール
| ID | ルール |
|---|---|
| BR-STATE-01 | Post/Notice は draft/published のみ（予約公開なし, F5=A） |
| BR-STATE-02 | 公開API一覧・詳細は status=published のみ返す |
| BR-STATE-03 | publishedAt は初回公開時に確定し、再公開で維持（一覧順序の安定） |
| BR-STATE-04 | Inquiry の初期状態=new。状態は new/in_progress/done 間で変更可（F2=B） |
| BR-STATE-05 | Post.authorDisplayName は作成時スナップショット。User改名/削除後も表示を維持 |

## お問い合わせ・通知ルール
| ID | ルール |
|---|---|
| BR-CONTACT-01 | 送信は入力検証・スパム対策通過が前提（BR-SEC-02） |
| BR-CONTACT-02 | 送信先メールは設定値（環境設定/後から変更可, CON-03）。ハードコード禁止 |
| BR-CONTACT-03 | SES送信失敗でも Inquiry 保存は成功扱い（記録優先）。失敗はログ＋リトライ対象 |
| BR-CONTACT-04 | ユーザーへの応答は汎用完了メッセージ（内部詳細を出さない, SECURITY-15） |

## セキュリティ・横断ルール
| ID | ルール |
|---|---|
| BR-SEC-01 | 秘密情報（送信先・鍵等）は Secrets Manager/設定で管理、コード/ログに出さない（SECURITY-12/03） |
| BR-SEC-02 | 公開エンドポイント（問い合わせ送信等）はレート制限/スロットリング（SECURITY-11） |
| BR-SEC-03 | 管理系の作成/更新/削除/状態変更は監査ログ（who/when/what, SECURITY-13/14） |
| BR-SEC-04 | 例外時は fail-closed（権限・検証を迂回しない）、汎用エラー応答（SECURITY-15） |
| BR-SEC-05 | リッチテキストは保存/表示でサニタイズ（XSS対策, SECURITY-05） |
| BR-SEC-06 | PII最小化：子供の氏名は保持/掲載しない。clientMeta は必要最小限 |

## 移行ルール（U4連携）
| ID | ルール |
|---|---|
| BR-MIG-01 | 移行記事は source=migrated、publishedAt=元記事日を保持 |
| BR-MIG-02 | 元記事識別子→postId のマップで重複投入を防止（冪等） |
| BR-MIG-03 | 画像は当面除外（Q14）。本文テキストの欠落は不可（検証） |

---

## テスト観点（PBT 部分適用の対象候補）
- **純粋関数**: 入力検証（長さ/形式/トリム）、リッチテキストのサニタイズ、抜粋生成、ページング計算
- **シリアライズ往復**: エンティティ⇔保存表現（DynamoDBアイテム）⇔API DTO の round-trip 同一性
- 上記は Property-Based Testing（部分適用）で検証（PBT-02/03/07/08/09）。
