"""配置加载：env 解析、白/黑名单、敏感词。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nonebot import get_driver

from .backends import BACKEND_DEFAULTS, get_endpoint, needs_api_key, resolve_edit_url
from .filters import match_nsfw

if TYPE_CHECKING:
    from nonebot.adapters import Event

__all__ = ["check_nsfw", "check_whitelist_blacklist", "get_config", "needs_api_key", "reset_config_cache"]

_config: dict | None = None


def reset_config_cache() -> None:
    """测试/热重载场景下清空缓存。"""
    global _config
    _config = None


def get_config() -> dict:
    global _config
    if _config is not None:
        return _config

    cfg = dict(get_driver().config)
    backend = cfg.get("draw_backend", "")

    txt2img_url = get_endpoint(backend, cfg.get("draw_api_url", ""), "txt2img")
    edits_url = resolve_edit_url(backend, txt2img_url, cfg.get("draw_api_url_edits", ""))

    api_key = cfg.get("draw_api_key", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    default_model = cfg.get("draw_model") or BACKEND_DEFAULTS.get(backend, {}).get("default_model", "flux")

    _config = {
        "api_url": txt2img_url,
        "api_url_edits": edits_url,
        "api_key": api_key,
        "model": default_model,
        "backend": backend,
        "default_size": cfg.get("draw_default_size", "1024x1024"),
        "timeout": cfg.get("draw_timeout", 120),
        "proxy": cfg.get("draw_proxy"),
        "nsfw_enabled": cfg.get("draw_nsfw_enabled", False),
        "nsfw_keywords": cfg.get("draw_nsfw_keywords", []),
        "nsfw_patterns": cfg.get("draw_nsfw_patterns", []),
        "whitelist_mode": cfg.get("draw_whitelist_mode", False),
        "whitelist": cfg.get("draw_whitelist", []),
        "blacklist": cfg.get("draw_blacklist", []),
        "quality": cfg.get("draw_quality"),
        "n": cfg.get("draw_n"),
        "user_cooldown": cfg.get("draw_user_cooldown", 60),
        "concurrent": cfg.get("draw_concurrent", False),
        "cache_enabled": cfg.get("draw_cache_enabled", False),
        "cache_dir": cfg.get("draw_cache_dir", "data/nonebot_plugin_easy_aidraw"),
        "cache_ttl": cfg.get("draw_cache_ttl", 86400),
        "prompt_max_chars": cfg.get("draw_prompt_max_chars", 4000),
        "headers": headers,
    }
    return _config


def check_whitelist_blacklist(event: Event) -> tuple[bool, str]:
    cfg = get_config()
    user_id = event.get_user_id()
    if cfg["whitelist_mode"]:
        return (user_id in cfg["whitelist"], "不在白名单中")
    return (user_id not in cfg["blacklist"], "在黑名单中")


def check_nsfw(prompt: str) -> tuple[bool, str | None]:
    cfg = get_config()
    return match_nsfw(
        prompt,
        keywords=cfg.get("nsfw_keywords", []),
        patterns=cfg.get("nsfw_patterns", []),
        enabled=cfg.get("nsfw_enabled", False),
    )
