"""敏感词/长度/文本归一化过滤器。"""

from __future__ import annotations

from functools import lru_cache
import re

__all__ = ["check_prompt_length", "match_nsfw", "normalize_text"]


@lru_cache(maxsize=1)
def _opencc_converter():
    try:
        from opencc import OpenCC  # type: ignore
    except Exception:
        return None
    try:
        return OpenCC("t2s")
    except Exception:
        return None


def normalize_text(text: str) -> str:
    """简繁归一 + 小写；未安装 opencc 时降级为纯小写。"""
    cc = _opencc_converter()
    base = cc.convert(text) if cc else text
    return base.lower()


def _compile_patterns(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns if p)


def match_nsfw(
    prompt: str,
    *,
    keywords: list[str],
    patterns: list[str],
    enabled: bool,
) -> tuple[bool, str | None]:
    """子串匹配 + 正则匹配；预编译缓存减少重复开销。"""
    if not enabled or not prompt:
        return False, None
    norm = normalize_text(prompt)
    for kw in keywords or ():
        if kw and kw.lower() in norm:
            return True, kw
    for compiled in _compile_patterns(tuple(patterns or ())):
        if compiled.search(norm):
            return True, compiled.pattern
    return False, None


def check_prompt_length(prompt: str, model: str, max_chars: int) -> tuple[bool, int]:
    """max_chars<=0 表示不限制。"""
    length = len(prompt)
    if max_chars <= 0:
        return True, length
    return (length <= max_chars, length)
