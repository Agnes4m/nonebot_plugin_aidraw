"""绘图 API 调用与配置访问"""

import base64
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import time
import uuid

import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger

from .models import ImageResponse

_config: dict | None = None

BACKEND_DEFAULTS = {
    "openai": {
        "base": "https://api.openai.com/v1",
        "txt2img": "/images/generations",
        "img2img": "/images/edits",
        "default_model": "gpt-image-2",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta",
        "txt2img": "/images/generations",
        "img2img": "/images/edits",
        "default_model": "gemini-pro",
    },
    "sd": {
        "base": "http://localhost:7860/sdapi/v1",
        "txt2img": "/txt2img",
        "img2img": "/img2img",
        "default_model": "sd15",
    },
}

KEY_NEEDED_BACKENDS = {"openai", "gemini"}


@dataclass
class UsageInfo:
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    def format(self) -> str:
        parts = [f"model={self.model}"]
        if self.input_tokens is not None:
            parts.append(f"in={self.input_tokens}")
        if self.output_tokens is not None:
            parts.append(f"out={self.output_tokens}")
        if self.total_tokens is not None:
            parts.append(f"total={self.total_tokens}")
        return ", ".join(parts)


def _normalize_base(url: str) -> str:
    url = url.rstrip("/")
    for suffix in ("/images/generations", "/images/edits"):
        if url.endswith(suffix):
            return url[: -len(suffix)]
    return url


def _get_config() -> dict:
    global _config
    if _config is not None:
        return _config

    cfg = dict(get_driver().config)
    backend = cfg.get("draw_backend", "")

    api_url_raw = cfg.get("draw_api_url", "")
    api_url_edits_raw = cfg.get("draw_api_url_edits", "")

    if api_url_raw:
        if not api_url_raw.startswith(("http://", "https://")):
            raise ValueError("draw_api_url 必须以 http:// 或 https:// 开头")
        api_url_raw = api_url_raw.rstrip("/")
        api_url_raw = _normalize_base(api_url_raw)
        if not api_url_raw.endswith("/v1"):
            raise ValueError("draw_api_url 必须以 /v1 结尾（如 https://apihub.agnes-ai.com/v1）")
        full_url = f"{api_url_raw}/images/generations"
    elif backend in BACKEND_DEFAULTS:
        full_url = BACKEND_DEFAULTS[backend]["base"] + BACKEND_DEFAULTS[backend]["txt2img"]
    else:
        raise ValueError("draw_api_url 或 draw_backend 必须设置其一")

    if api_url_edits_raw:
        if not api_url_edits_raw.startswith(("http://", "https://")):
            raise ValueError("draw_api_url_edits 必须以 http:// 或 https:// 开头")
        edits_url = _normalize_base(api_url_edits_raw)
        if not edits_url.endswith("/v1"):
            raise ValueError("draw_api_url_edits 必须以 /v1 结尾")
        edits_full = f"{edits_url}/images/edits"
    elif backend in BACKEND_DEFAULTS:
        edits_full = BACKEND_DEFAULTS[backend]["base"] + BACKEND_DEFAULTS[backend]["img2img"]
    else:
        edits_full = full_url.replace("/images/generations", "/images/edits")

    model = cfg.get("draw_model") or BACKEND_DEFAULTS.get(backend, {}).get("default_model", "flux")

    headers = {"Content-Type": "application/json"}
    api_key = cfg.get("draw_api_key", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    _config = {
        "api_url": full_url,
        "api_url_edits": edits_full,
        "api_key": api_key,
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
        "user_cooldown": cfg.get("draw_user_cooldown", 60),
        "cache_enabled": cfg.get("draw_cache_enabled", False),
        "cache_dir": cfg.get("draw_cache_dir", "data/nonebot_plugin_easy_aidraw"),
        "cache_ttl": cfg.get("draw_cache_ttl", 86400),
        "headers": headers,
    }
    return _config


def _clear_config() -> None:
    global _config
    _config = None


def is_private_message(event: Event) -> bool:
    return not event.get_session_id().startswith(("group_", "channel_"))


def check_whitelist_blacklist(event: Event) -> tuple[bool, str]:
    cfg = _get_config()
    user_id = event.get_user_id()

    if cfg["whitelist_mode"]:
        return (user_id in cfg["whitelist"], "不在白名单中")
    return (user_id not in cfg["blacklist"], "在黑名单中")


def check_nsfw(prompt: str) -> tuple[bool, str | None]:
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


def _safe_headers(headers: dict) -> dict:
    return {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()}


def _save_b64_to_cache(b64: str) -> Path:
    cfg = _get_config()
    cache_dir = Path(cfg["cache_dir"]) / date.today().isoformat()
    cache_dir.mkdir(parents=True, exist_ok=True)
    img_path = cache_dir / f"{uuid.uuid4().hex}.png"
    img_path.write_bytes(base64.b64decode(b64))
    logger.info(f"[绘图] 已保存缓存: {img_path}")
    return img_path


async def _download_to_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


def _b64_to_result(b64: str) -> Path:
    cfg = _get_config()
    if cfg["cache_enabled"]:
        return _save_b64_to_cache(b64)
    cache_path = Path(cfg["cache_dir"]) / f".tmp-{uuid.uuid4().hex}.png"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(base64.b64decode(b64))
    return cache_path


def _extract_image_data(resp: ImageResponse) -> str | Path:
    if not resp.data:
        safe = resp.model_dump(exclude={"usage"}, exclude_none=True)
        raise ValueError(f"API 返回格式异常: {safe}")
    img_data = resp.data[0]
    if img_data.b64_json:
        return _b64_to_result(img_data.b64_json)
    if img_data.url:
        return img_data.url
    raise ValueError("API 未返回图片 URL 或 b64_json")


def _build_usage_info(resp: ImageResponse, cfg: dict) -> UsageInfo:
    if resp.usage or resp.model:
        return UsageInfo(
            model=resp.model or cfg["model"],
            input_tokens=resp.usage.input_tokens if resp.usage else None,
            output_tokens=resp.usage.output_tokens if resp.usage else None,
            total_tokens=resp.usage.total_tokens if resp.usage else None,
        )
    return UsageInfo(model=cfg["model"])


def _sanitize_for_log(obj):
    if isinstance(obj, dict):
        return {k: ("<bytes>" if k in ("b64_json",) else _sanitize_for_log(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_log(i) for i in obj]
    return obj


def _format_error(status: int, body: str) -> str:
    if not body:
        return f"API 返回 {status}"
    return f"API 返回 {status}: {body}"


async def _post_with_retry(client: httpx.AsyncClient, *, url: str, headers: dict, **kwargs) -> ImageResponse:
    try:
        response = await client.post(url, headers=headers, **kwargs)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        body = e.response.text or ""
        try:
            err = e.response.json().get("error", {})
            code = err.get("code", "")
            msg = err.get("message", body)
            if code and msg:
                body = f"[{code}] {msg}"
            elif msg:
                body = msg
        except Exception:
            pass
        raise RuntimeError(_format_error(e.response.status_code, body.strip())) from e

    resp = ImageResponse.model_validate(response.json())
    logger.info(f"[绘图] 响应: {_sanitize_for_log(resp.model_dump(exclude_none=True))}")
    return resp


def _build_json_payload(cfg: dict, prompt: str) -> dict:
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
    return payload


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict, headers: dict) -> ImageResponse:
    logger.debug(f"[绘图] 请求体: {payload}")
    logger.debug(f"[绘图] headers: {_safe_headers(headers)}")
    return await _post_with_retry(client, url=url, headers=headers, json=payload)


async def generate_image(prompt: str) -> tuple[str | Path, UsageInfo]:
    cfg = _get_config()
    if cfg["backend"] in KEY_NEEDED_BACKENDS and not cfg["api_key"]:
        raise ValueError("未配置 DRAW_API_KEY")

    payload = _build_json_payload(cfg, prompt)
    client_kwargs: dict = {"timeout": cfg["timeout"]}
    if cfg.get("proxy"):
        client_kwargs["proxy"] = cfg["proxy"]

    async with httpx.AsyncClient(**client_kwargs) as client:
        logger.info(f"[绘图] 请求: model={cfg['model']}, prompt_len={len(prompt)}, mode=txt2img")
        resp = await _post_json(client, cfg["api_url"], payload, cfg["headers"])
        result = _extract_image_data(resp)
        usage_info = _build_usage_info(resp, cfg)
        logger.info(f"[绘图] 生成成功: {result}")
        return result, usage_info


async def edit_image(prompt: str, image_url: str) -> tuple[str | Path, UsageInfo]:
    cfg = _get_config()
    if cfg["backend"] in KEY_NEEDED_BACKENDS and not cfg["api_key"]:
        raise ValueError("未配置 DRAW_API_KEY")

    logger.info(f"[绘图] 准备垫图: {image_url}")
    image_bytes = await _download_to_bytes(image_url)

    client_kwargs: dict = {"timeout": cfg["timeout"]}
    if cfg.get("proxy"):
        client_kwargs["proxy"] = cfg["proxy"]

    form_data: dict = {
        "model": cfg["model"],
        "prompt": prompt,
        "n": str(cfg.get("n") or 1),
    }
    if cfg["backend"] == "openai":
        form_data["quality"] = cfg.get("quality") or "standard"
    if fmt := cfg.get("response_format"):
        form_data["response_format"] = fmt

    files = {"image": ("image.png", image_bytes, "image/png")}
    headers = {"Authorization": cfg["headers"]["Authorization"]} if cfg["headers"].get("Authorization") else {}

    async with httpx.AsyncClient(**client_kwargs) as client:
        logger.info(f"[绘图] 请求: model={cfg['model']}, prompt_len={len(prompt)}, mode=img2img")
        resp = await _post_with_retry(client, url=cfg["api_url_edits"], headers=headers, data=form_data, files=files)
        result = _extract_image_data(resp)
        usage_info = _build_usage_info(resp, cfg)
        logger.info(f"[绘图] 生成成功: {result}")
        return result, usage_info


def cleanup_cache(ttl: int | None = None) -> tuple[int, int]:
    cfg = _get_config()
    cache_root = Path(cfg["cache_dir"])
    if not cache_root.exists():
        return 0, 0
    expire_sec = ttl if ttl is not None else cfg["cache_ttl"]
    threshold = time.time() - expire_sec
    deleted = 0
    remaining = 0
    for p in cache_root.rglob("*.png"):
        try:
            if p.stat().st_mtime < threshold:
                p.unlink()
                deleted += 1
            else:
                remaining += 1
        except OSError as e:
            logger.warning(f"[绘图] 清理失败 {p}: {e}")
    logger.info(f"[绘图] 缓存清理: 删除={deleted}, 剩余={remaining}")
    return deleted, remaining
