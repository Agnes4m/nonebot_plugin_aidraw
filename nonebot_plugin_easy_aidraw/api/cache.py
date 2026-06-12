"""b64 落盘与缓存清理。"""

from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import time
import uuid

from nonebot.log import logger

from .config_loader import get_config

__all__ = ["b64_to_path", "cleanup_cache", "temp_b64_path"]

_CACHE_EXT = frozenset({".png", ".jpg", ".jpeg", ".webp", ".tmp"})


def _decode(b64: str) -> bytes:
    return base64.b64decode(b64)


@contextmanager
def temp_b64_path(b64: str):
    cfg = get_config()
    path = Path(cfg["cache_dir"]) / f".tmp-{uuid.uuid4().hex}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_decode(b64))
    try:
        yield path
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"[绘图] 临时文件清理失败 {path}: {e}")


def _write_temp(b64: str) -> tuple[Path, bool]:
    cfg = get_config()
    path = Path(cfg["cache_dir"]) / f".tmp-{uuid.uuid4().hex}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_decode(b64))
    return path, True


def b64_to_path(b64: str) -> tuple[Path, bool]:
    """返回 (path, is_temporary)。is_temporary=True 时调用方负责删除。"""
    cfg = get_config()
    if cfg["cache_enabled"]:
        cache_dir = Path(cfg["cache_dir"]) / date.today().isoformat()
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = cache_dir / f"{uuid.uuid4().hex}.png"
        path.write_bytes(_decode(b64))
        logger.info(f"[绘图] 已保存缓存: {path}")
        return path, False
    return _write_temp(b64)


def cleanup_cache(ttl: int | None = None) -> tuple[int, int]:
    cfg = get_config()
    cache_root = Path(cfg["cache_dir"])
    if not cache_root.exists():
        return 0, 0
    threshold = time.time() - (ttl if ttl is not None else cfg["cache_ttl"])
    deleted = remaining = 0
    for p in cache_root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in _CACHE_EXT:
            continue
        try:
            if p.stat().st_mtime < threshold:
                p.unlink()
                deleted += 1
            else:
                remaining += 1
        except OSError as e:
            logger.warning(f"[绘图] 清理失败 {p}: {e}")
    for d in sorted(cache_root.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()
            except OSError:
                pass
    logger.info(f"[绘图] 缓存清理: 删除={deleted}, 剩余={remaining}")
    return deleted, remaining
