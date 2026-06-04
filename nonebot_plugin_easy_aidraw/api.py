"""绘图 API 调用与配置访问"""

import base64
from pathlib import Path
import re
import uuid

import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger

from .models import ImageResponse

_config: dict | None = None

BACKEND_DEFAULTS = {
    "openai": "https://api.openai.com/v1/images/generations",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/images/generations",
    "sd": "http://localhost:7860/sdapi/v1/txt2img",
}

BACKEND_MODELS = {
    "openai": "gpt-image-2",
    "gemini": "gemini-pro",
    "sd": "sd15",
}


def _get_config() -> dict:
    """延迟获取配置"""
    global _config
    if _config is not None:
        return _config

    cfg = dict(get_driver().config)
    backend = cfg.get("draw_backend", "")
    api_url = cfg.get("draw_api_url", "")
    model = cfg.get("draw_model", "") or BACKEND_MODELS.get(backend, "flux")

    if backend and api_url:
        base = BACKEND_DEFAULTS.get(backend, "").rsplit("/", 1)[0]
        full_url = api_url if api_url.startswith("http") else f"{base}/{api_url}"
    elif backend:
        full_url = BACKEND_DEFAULTS.get(backend, "")
    elif api_url:
        full_url = api_url if api_url.startswith("http") else api_url
    else:
        raise ValueError("draw_api_url 或 draw_backend 必须设置其一")

    headers = {"Content-Type": "application/json"}
    if backend == "openai":
        headers["Authorization"] = f"Bearer {cfg.get('draw_api_key', '')}"

    _config = {
        "api_url": full_url,
        "api_key": cfg.get("draw_api_key", ""),
        "model": model,
        "backend": backend,
        "default_size": cfg.get("draw_default_size", "1024x1024"),
        "timeout": cfg.get("draw_timeout", 120),
        "proxy": cfg.get("draw_proxy"),
        "nsfw_enabled": cfg.get("draw_nsfw_enabled", False),
        "nsfw_keywords": cfg.get("draw_nsfw_keywords", []),
        "whitelist_mode": cfg.get("draw_whitelist_mode", False),
        "whitelist": cfg.get("draw_whitelist", []),
        "blacklist": cfg.get("draw_blacklist", []),
        "quality": cfg.get("draw_quality"),
        "n": cfg.get("draw_n"),
        "response_format": cfg.get("draw_response_format"),
        "headers": headers,
    }
    return _config


def _clear_config() -> None:
    """清除缓存的配置，供测试用"""
    global _config
    _config = None


def is_private_message(event: Event) -> bool:
    """判断是否为私聊消息"""
    return not event.get_session_id().startswith(("group_", "channel_"))


def check_whitelist_blacklist(event: Event) -> tuple[bool, str]:
    """检查黑白名单"""
    cfg = _get_config()
    session_id = event.get_session_id()
    target_id = (
        f"group_{session_id.split('_', 1)[1]}" if session_id.startswith("group_") else session_id.split("_", 1)[-1]
    )

    if cfg["whitelist_mode"]:
        return (target_id in cfg["whitelist"], "不在白名单中")
    return (target_id not in cfg["blacklist"], "在黑名单中")


def check_nsfw(prompt: str) -> tuple[bool, str | None]:
    """检查 NSFW 关键词"""
    cfg = _get_config()
    if not cfg.get("nsfw_enabled"):
        return False, None
    keywords = cfg.get("nsfw_keywords", [])
    if not keywords:
        return False, None
    words = re.findall(r"[\w\u4e00-\u9fff]+", prompt.lower())
    nsfw_set = {kw.lower() for kw in keywords}
    for word in words:
        if word in nsfw_set:
            return True, word
    return False, None


def _truncate(val: str, length: int = 100) -> str:
    return val[:length] + "..." if len(val) > length else val


def _log_payload(payload: dict) -> None:
    def _sanitize(v: str) -> str:
        if len(v) > 100:
            return _truncate(v, 100)
        return v

    log: dict = {}
    for k, v in payload.items():
        if k == "extra_body":
            log[k] = {kk: _sanitize(str(vv)) for kk, vv in v.items()} if isinstance(v, dict) else v
        else:
            log[k] = _sanitize(v) if isinstance(v, str) else v
    logger.debug(f"[绘图] 请求体: {log}")


async def generate_image(prompt: str, image_urls: list[str] | None = None) -> str | Path:
    """调用 API 生成图片，返回 URL 或本地路径"""
    cfg = _get_config()

    if not cfg["api_key"]:
        raise ValueError("未配置 DRAW_API_KEY")

    payload: dict = {
        "model": cfg["model"],
        "prompt": prompt,
        "size": cfg["default_size"],
    }

    if cfg["backend"] == "openai":
        payload["n"] = cfg.get("n") or 1
        payload["quality"] = cfg.get("quality") or "standard"
        if fmt := cfg.get("response_format"):
            payload["response_format"] = fmt

    if image_urls:
        payload["extra_body"] = {"image": image_urls}

    client_kwargs: dict = {"timeout": cfg["timeout"]}
    if cfg.get("proxy"):
        client_kwargs["proxy"] = cfg["proxy"]

    _log_payload(payload)

    async with httpx.AsyncClient(**client_kwargs) as client:
        logger.info(f"[绘图] 请求: model={cfg['model']}, prompt_len={len(prompt)}")
        response = await client.post(cfg["api_url"], json=payload, headers=cfg["headers"])
        response.raise_for_status()

        resp = ImageResponse.model_validate(response.json())

        def _sanitize_json(obj):
            if isinstance(obj, str):
                return _truncate(obj, 100)
            if isinstance(obj, dict):
                return {k: _sanitize_json(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize_json(item) for item in obj]
            return obj

        logger.debug(f"[绘图] 响应: {_sanitize_json(resp.model_dump())}")

        if not resp.data:
            raise ValueError(f"API 返回格式异常: {resp}")

        img_data = resp.data[0]

        if img_data.url:
            return img_data.url

        if img_data.b64_json:
            cache_dir = Path("data/nonebot_plugin_easy_aidraw")
            cache_dir.mkdir(parents=True, exist_ok=True)
            img_path = cache_dir / f"{uuid.uuid4().hex}.png"
            img_path.write_bytes(base64.b64decode(img_data.b64_json))
            logger.info(f"[绘图] 已保存本地: {img_path}")
            return img_path

        raise ValueError("API 未返回图片 URL 或 b64_json")
