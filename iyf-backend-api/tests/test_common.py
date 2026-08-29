"""common モジュールのユニットテスト＋PBT（純粋関数）。"""
from __future__ import annotations

from hypothesis import given, strategies as st

from src.common.logging import mask_pii
from src.common.validation import clamp_limit, sanitize_text


def test_mask_pii_masks_sensitive_keys():
    data = {"email": "a@example.com", "name": "太郎", "post_id": "p1"}
    masked = mask_pii(data)
    assert masked["email"] == "***"
    assert masked["name"] == "***"
    assert masked["post_id"] == "p1"  # 非PIIはそのまま


def test_mask_pii_nested():
    data = {"payload": {"message": "秘密", "count": 3}}
    masked = mask_pii(data)
    assert masked["payload"]["message"] == "***"
    assert masked["payload"]["count"] == 3


def test_sanitize_text_escapes_html():
    assert sanitize_text("  <script>alert(1)</script>  ") == (
        "&lt;script&gt;alert(1)&lt;/script&gt;"
    )


# ---- PBT: clamp_limit は常に [1, maximum] に収まる ----
@given(
    requested=st.one_of(st.none(), st.integers(min_value=-1000, max_value=1000)),
    default=st.integers(min_value=1, max_value=50),
    maximum=st.integers(min_value=1, max_value=50),
)
def test_clamp_limit_within_bounds(requested, default, maximum):
    result = clamp_limit(requested, default, maximum)
    assert 1 <= result <= maximum
    if requested is None:
        # None のときは default を使うが、上限 maximum で丸める。
        assert result == min(default, maximum)


# ---- PBT: sanitize_text は冪等（2回適用しても山カッコは増えない）を保つ性質 ----
@given(st.text(max_size=200))
def test_sanitize_text_removes_raw_angle_brackets(s):
    out = sanitize_text(s)
    assert "<" not in out
    assert ">" not in out
