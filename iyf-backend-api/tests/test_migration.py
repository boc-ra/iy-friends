"""U4 移行ツールのテスト（正規化・冪等取り込み）。スクレイピングはフィクスチャで代替。"""
from __future__ import annotations

from migration.importer import ImportReport, import_posts, make_post_id, to_post
from migration.normalize import RawPost, normalize, parse_date, strip_html


# ---- 正規化 ----

def test_strip_html_excludes_images():
    html = '<p>こんにちは<img src="x.jpg">世界</p><p>次段落</p>'
    text = strip_html(html, exclude_images=True)
    assert "img" not in text
    assert "こんにちは" in text and "世界" in text
    assert "次段落" in text


def test_parse_date_multiple_formats():
    for s in ["2024-05-01", "2024/05/01", "2024年05月01日", "2024-05-01 10:30:00"]:
        iso, epoch = parse_date(s)
        assert iso is not None and epoch is not None and epoch > 0


def test_parse_date_unparseable():
    iso, epoch = parse_date("なんとなく去年")
    assert iso is None and epoch is None


def test_normalize_basic():
    raw = RawPost(
        source_url="https://example.com/blog/1",
        title="<b>初投稿</b>",
        body_html="<p>本文<img src='a.png'>です</p>",
        date_str="2024-05-01",
        author="コーチ山田",
    )
    pi = normalize(raw, default_author="IYフレンズ", exclude_images=True)
    assert pi.title == "初投稿"
    assert "本文" in pi.body and "img" not in pi.body
    assert pi.author_display_name == "コーチ山田"
    assert pi.published_at_epoch > 0
    assert pi.warnings == []


def test_normalize_defaults_author_and_flags_bad_date():
    raw = RawPost(source_url="u", title="t", body_html="<p>b</p>", date_str=None, author=None)
    pi = normalize(raw, default_author="IYフレンズ")
    assert pi.author_display_name == "IYフレンズ"
    assert "date-unparsed" in pi.warnings


# ---- 取り込み（冪等） ----

class _FakeRepo:
    def __init__(self, existing_ids=()):
        self.saved = []
        self._existing = set(existing_ids)

    def get_post(self, post_id):
        return object() if post_id in self._existing else None

    def put(self, item):
        self.saved.append(item)
        self._existing.add(item["post_id"])


def _pi(url):
    raw = RawPost(source_url=url, title="t", body_html="<p>b</p>", date_str="2024-05-01")
    return normalize(raw, default_author="IYフレンズ")


def test_make_post_id_deterministic():
    assert make_post_id("https://x/1") == make_post_id("https://x/1 ")
    assert make_post_id("https://x/1") != make_post_id("https://x/2")


def test_import_is_idempotent():
    repo = _FakeRepo()
    inputs = [_pi("https://x/1"), _pi("https://x/2")]
    r1 = import_posts(inputs, repo, publish_status="published")
    assert r1.imported == 2 and r1.skipped_duplicate == 0
    assert len(repo.saved) == 2
    # 再実行 → 全て重複扱い、新規保存なし。
    r2 = import_posts(inputs, repo, publish_status="published")
    assert r2.imported == 0 and r2.skipped_duplicate == 2
    assert len(repo.saved) == 2


def test_import_published_and_source_migrated():
    post = to_post(_pi("https://x/9"), publish_status="published")
    assert post.status.value == "published"
    assert post.source == "migrated"
    assert post.source_url == "https://x/9"
    assert post.post_id.startswith("mig-")


def test_dry_run_does_not_save():
    repo = _FakeRepo()
    report = import_posts([_pi("https://x/1")], repo, dry_run=True)
    assert report.imported == 1
    assert repo.saved == []   # dry-run は保存しない
