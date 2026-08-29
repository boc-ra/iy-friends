"""スクレイパ（アダプタ方式, Q-M1=A）。

現行サイトから記事を収集する。HTML構造は config の CSS セレクタで差し替える。
requests / beautifulsoup4 が必要（移行時のみ）。未インストール時は明示エラー。

礼儀・負荷配慮: request_delay_seconds で間隔を空ける。
"""
from __future__ import annotations

import time
from urllib.parse import urljoin

from migration.normalize import RawPost

try:
    import requests
    from bs4 import BeautifulSoup
    _DEPS_OK = True
except Exception:  # noqa: BLE001
    _DEPS_OK = False


def _require_deps() -> None:
    if not _DEPS_OK:
        raise RuntimeError(
            "スクレイピングには requests と beautifulsoup4 が必要です。"
            " `pip install requests beautifulsoup4` を実行してください。"
        )


def _fetch(url: str, *, user_agent: str, timeout: int = 20) -> str:
    resp = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def collect_article_links(config: dict) -> list[str]:
    """一覧ページを巡回し、記事詳細URLを収集する。"""
    _require_deps()
    src = config["source"]
    sel = config["selectors"]
    ua = src.get("user_agent", "iyf-blog-migration/1.0")
    delay = float(src.get("request_delay_seconds", 1.0))
    max_pages = int(src.get("max_pages", 1))

    links: list[str] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        list_url = src["list_url"].format(page=page)
        html = _fetch(list_url, user_agent=ua)
        soup = BeautifulSoup(html, "html.parser")
        anchors = soup.select(sel["list_item_link"])
        if not anchors:
            break  # これ以上ページがない
        for a in anchors:
            href = a.get("href")
            if not href:
                continue
            full = urljoin(list_url, href)
            if full not in seen:
                seen.add(full)
                links.append(full)
        time.sleep(delay)
    return links


def scrape_article(url: str, config: dict) -> RawPost:
    """記事詳細ページを1件スクレイプして RawPost に。"""
    _require_deps()
    src = config["source"]
    sel = config["selectors"]
    ua = src.get("user_agent", "iyf-blog-migration/1.0")

    html = _fetch(url, user_agent=ua)
    soup = BeautifulSoup(html, "html.parser")

    def _text(selector: str) -> str:
        el = soup.select_one(selector) if selector else None
        return el.get_text(" ", strip=True) if el else ""

    def _inner_html(selector: str) -> str:
        el = soup.select_one(selector) if selector else None
        return el.decode_contents() if el else ""

    # 日付は datetime 属性優先、なければテキスト。
    date_el = soup.select_one(sel.get("date", "")) if sel.get("date") else None
    date_str = None
    if date_el is not None:
        date_str = date_el.get("datetime") or date_el.get_text(strip=True)

    return RawPost(
        source_url=url,
        title=_text(sel.get("title", "")),
        body_html=_inner_html(sel.get("body", "")),
        date_str=date_str,
        author=_text(sel.get("author", "")) or None,
    )


def scrape_source(config: dict, *, limit: int | None = None) -> list[RawPost]:
    """一覧→詳細を辿って RawPost のリストを返す。"""
    _require_deps()
    delay = float(config["source"].get("request_delay_seconds", 1.0))
    links = collect_article_links(config)
    if limit is not None:
        links = links[:limit]
    posts: list[RawPost] = []
    for url in links:
        posts.append(scrape_article(url, config))
        time.sleep(delay)
    return posts
