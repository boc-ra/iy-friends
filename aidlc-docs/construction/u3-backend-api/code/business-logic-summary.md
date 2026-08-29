# ビジネスロジック レイヤ 要約

各モジュールの `models.py`（Pydantic）＋ `service.py`（業務ロジック）。

| モジュール | モデル | サービス要点 | ストーリー |
|---|---|---|---|
| content | Post, Notice（status: draft/published） | 公開のみ一覧(10件)・詳細（draftは404で秘匿） | US-01/04/05/06/08 |
| calendar | Event | 公開のみ・日付昇順一覧・詳細 | US-10 |
| contact | InquiryCreate（入力）/ Inquiry（永続） | 検証→軽量冪等→保存→SES同期通知(ベストエフォート) | US-13 |

ビジネスルール反映: BR-STATE（公開状態）、BR-SEC（存在秘匿）、BR-CONTACT（受付フロー）、BR-VAL（検証）。
テスト: `test_content.py` / `test_calendar.py` / `test_contact.py`（状態遷移・公開フィルタ・冪等・PBT往復）。
