"""内置 Counter：把绘图调用指标写日志，零依赖。"""

from __future__ import annotations

from collections import Counter
from threading import Lock

from nonebot.log import logger

__all__ = ["metrics"]

_lock = Lock()
_counters: Counter[str] = Counter()


def _inc(name: str, value: int = 1) -> None:
    with _lock:
        _counters[name] += value


def _snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counters)


class Metrics:
    @staticmethod
    def hit(event: str) -> None:
        _inc(event)

    @staticmethod
    def dump() -> None:
        data = _snapshot()
        if not data:
            return
        line = " | ".join(f"{k}={v}" for k, v in sorted(data.items()))
        logger.info(f"[绘图指标] {line}")

    @staticmethod
    def snapshot() -> dict[str, int]:
        return _snapshot()


metrics = Metrics()
