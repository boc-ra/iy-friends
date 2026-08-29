"""正規化: スクレイプした生記事 → 投入用 PostInput。

- タイトル/本文のサニタイズ（SECURITY-05）、投稿日パース（JST）、著者表示名。
- 画像は当面除外（Q14）。純粋関数中心で PBT/ユニットテスト対象。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

# 対応する日付フォーマット（現行サイトの表記ゆれを吸収）。
_DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y年%m月%d日",
]

_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t　]+")


@dataclass
class RawPost:
    """スクレイパが返す生データ。"""

    source_url: str
    title: str
    body_html: str
    date_str: str | None = None
    author: str | None = None


@dataclass
class PostInput:
    """正規化済みの投入データ。"""

    source_url: str
    title: str
    body: str
    author_display_name: str
    published_at_iso: str
    published_at_epoch: int
    warnings: list[str] = field(default_factory=list)


def strip_html(html: str, *, exclude_images: bool = True) -> str:
    """HTML からテキストを抽出する純粋関数。exclude_images 時は img を除去。

    タグを除去し、連続空白を整理する。移行用の簡易実装。
    """
    text = html
    if exclude_images:
        text = _IMG_TAG.sub("", text)
    # 段落/改行をスペースに寄せてからタグ除去。
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = _TAG.sub("", text)
    text = _WS.sub(" ", text)
    # 3連以上の改行を2つに。
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_date(date_str: str | None) -> tuple[str | None, int | None]:
    """日付文字列を (ISO8601(JST), epoch秒) に。失敗時は (None, None)。純粋関数。"""
    if not date_str:
        return None, None
    s = date_str.strip()
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=JST)
            return dt.astimezone(JST).isoformat(), int(dt.timestamp())
        except ValueError:
            continue
    return None, None


def normalize(raw: RawPost, *, default_author: str, exclude_images: bool = True) -> PostInput:
    """生記事を投入用に正規化する。"""
    warnings: list[str] = []

    title = _WS.sub(" ", _TAG.sub("", raw.title)).strip()
    if not title:
        title = "(無題)"
        warnings.append("title-empty")

    body = strip_html(raw.body_html, exclude_images=exclude_images)
    if not body:
        warnings.append("body-empty")

    author = (raw.author or "").strip() or default_author

    published_iso, published_epoch = parse_date(raw.date_str)
    if published_epoch is None:
        # 日付不明はエポック0扱いにせず、警告を付けて呼び出し側で判断させる。
        warnings.append("date-unparsed")
        published_iso, published_epoch = None, 0

    return PostInput(
        source_url=raw.source_url,
        title=title[:200],
        body=body[:100_000],
        author_display_name=author[:60],
        published_at_iso=published_iso or "",
        published_at_epoch=published_epoch or 0,
        warnings=warnings,
    )
