"""绘图 API 调用与配置访问"""

from __future__ import annotations

import re

import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger

_config: dict | None = None

BACKEND_BASES = {
    "openai": "https://api.openai.com",
    "gemini": "https://generativelanguage.googleapis.com",
    "sd": "http://localhost:7860",
}

BACKEND_PATHS = {
    "openai": "/v1/images/generations",
    "gemini": "/v1beta/images/generations",
    "sd": "/sdapi/v1/txt2img",
}

BACKEND_HEADERS = {
    "openai": {
        "Content-Type": "application/json",
        "OpenAI-Organization": "",
    },
    "gemini": {
        "Content-Type": "application/json",
    },
    "sd": {
        "Content-Type": "application/json",
    },
}

BACKEND_DEFAULTS = {
    "openai": "flux",
    "gemini": "gemini-pro",
    "sd": "sd15",
}


def _get_config() -> dict:
    """延迟获取配置"""
    global _config
    if _config is None:
        config_dict = dict(get_driver().config)
        api_url = config_dict.get("draw_api_url", "")
        backend = config_dict.get("draw_backend", "")
        model = config_dict.get("draw_model", "")

        if backend:
            base = BACKEND_BASES.get(backend, "")
            path = BACKEND_PATHS.get(backend, "")
            if api_url:
                full_url = api_url if api_url.startswith("http") else base.rstrip("/") + "/" + api_url.lstrip("/")
            else:
                full_url = base + path
            headers = BACKEND_HEADERS.get(backend, {"Content-Type": "application/json"}).copy()
            if headers.get("OpenAI-Organization") == "":
                del headers["OpenAI-Organization"]
            if not model:
                model = BACKEND_DEFAULTS.get(backend, "flux")
        else:
            if not api_url:
                raise ValueError("draw_api_url 或 draw_backend 必须设置其一")
            full_url = api_url if api_url.startswith("http") else api_url
            headers = {"Content-Type": "application/json"}
            if not model:
                model = "flux"

        _config = {
            "api_url": full_url,
            "api_key": config_dict.get("draw_api_key", ""),
            "model": model,
            "default_size": config_dict.get("draw_default_size", "1024x1024"),
            "timeout": config_dict.get("draw_timeout", 120),
            "nsfw_enabled": config_dict.get("draw_nsfw_enabled", False),
            "nsfw_keywords": config_dict.get("draw_nsfw_keywords", []),
            "headers": headers,
            "backend": backend,
            # OpenAI 专用参数
            "quality": config_dict.get("draw_quality"),
            "n": config_dict.get("draw_n"),
            "thinking": config_dict.get("draw_thinking"),
            "response_format": config_dict.get("draw_response_format"),
            "user": config_dict.get("draw_user"),
            "background": config_dict.get("draw_background"),
            "seed": config_dict.get("draw_seed"),
            "proxy": config_dict.get("draw_proxy"),
        }
    return _config


def is_private_message(event: Event) -> bool:
    """判断是否为私聊消息"""
    session_id = event.get_session_id()
    return not session_id.startswith(("group_", "channel_"))


def check_whitelist_blacklist(event: Event) -> tuple[bool, str]:
    """检查黑白名单，返回 (是否通过, 原因)"""
    config = _get_config()
    session_id = event.get_session_id()

    if session_id.startswith("group_"):
        target_id = "group_" + session_id.split("_")[1]
    else:
        target_id = session_id.split("_", 1)[-1]

    whitelist = config.get("draw_whitelist", [])
    blacklist = config.get("draw_blacklist", [])
    whitelist_mode = config.get("draw_whitelist_mode", False)

    if whitelist_mode:
        if target_id not in whitelist:
            return False, "不在白名单中"
        return True, ""
    else:
        if target_id in blacklist:
            return False, "在黑名单中"
        return True, ""


def check_nsfw(prompt: str) -> tuple[bool, str | None]:
    """检查 prompt 是否包含 NSFW 关键词"""
    config = _get_config()

    if not config.get("nsfw_enabled", False):
        return False, None

    nsfw_keywords = config.get("nsfw_keywords", [])
    if not nsfw_keywords:
        return False, None

    words = re.findall(r"[\w\u4e00-\u9fff]+", prompt.lower())

    nsfw_set = {kw.lower() for kw in nsfw_keywords}
    for word in words:
        if word in nsfw_set:
            return True, word

    return False, None


async def generate_image(prompt: str, image_urls: list[str] | None = None) -> str | None:
    """调用API生成图片，返回图片URL"""
    config = _get_config()

    if not config["api_key"]:
        raise ValueError("未配置 DRAW_API_KEY，请检查配置文件")

    headers = config["headers"].copy()
    headers["Authorization"] = f"Bearer {config['api_key']}"

    payload = {
        "model": config["model"],
        "prompt": prompt,
        "size": config["default_size"],
    }

    # OpenAI 专用参数（必填）
    if config["backend"] == "openai":
        payload["n"] = config.get("n") or 1
        payload["quality"] = config.get("quality") or "standard"
        if config.get("thinking"):
            payload["thinking"] = config["thinking"]
        if config.get("response_format"):
            payload["response_format"] = config["response_format"]
        if config.get("user"):
            payload["user"] = config["user"]
        if config.get("background"):
            payload["background"] = config["background"]
        if config.get("seed") is not None:
            payload["seed"] = config["seed"]

    if image_urls:
        payload["extra_body"] = {
            "image": image_urls,
            "response_format": config.get("response_format") or "url",
        }

    client_kwargs = {"timeout": config["timeout"]}
    if config.get("proxy"):
        client_kwargs["proxy"] = config["proxy"]
    async with httpx.AsyncClient(**client_kwargs) as client:
        logger.info(
            f"[绘图] 发起请求: url={config['api_url']}, "
            f"model={config['model']}, prompt_len={len(prompt)}, "
            f"size={config['default_size']}, image_count={len(image_urls) if image_urls else 0}"
        )
        logger.debug(f"[绘图] 请求体: {payload}")
        logger.debug(f"[绘图] 请求头: {headers}")
        response = await client.post(config["api_url"], json=payload, headers=headers)
        logger.info(f"[绘图] 响应状态: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        log_data = {k: v for k, v in data.items() if k != "data"}
        if "data" in data:
            d = data["data"]
            if isinstance(d, list) and len(d) > 0:
                first = d[0]
                log_data["data"] = {
                    k: (f"<{len(v)} chars>" if k == "b64_json" and isinstance(v, str) else v) for k, v in first.items()
                }
            elif isinstance(d, dict):
                log_data["data"] = {
                    k: (f"<{len(v)} chars>" if k == "b64_json" and isinstance(v, str) else v) for k, v in d.items()
                }
        logger.debug(f"[绘图] API返回: {log_data}")

        img_data = None
        if isinstance(data.get("data"), list) and len(data["data"]) > 0:
            img_data = data["data"][0]
        elif isinstance(data.get("data"), dict):
            img_data = data["data"]

        if not img_data:
            raise ValueError(f"API返回格式异常: {data}")

        if url := img_data.get("url"):
            return url

        if b64 := img_data.get("b64_json"):
            import base64
            from pathlib import Path
            import uuid

            img_bytes = base64.b64decode(b64)
            cache_dir = Path("data/nonebot_plugin_easy_aidraw")
            cache_dir.mkdir(parents=True, exist_ok=True)
            img_path = cache_dir / f"{uuid.uuid4().hex}.png"
            img_path.write_bytes(img_bytes)
            logger.info(f"[绘图] 图片已保存到本地: {img_path}")
            return str(img_path)

        raise ValueError("API未返回图片URL或b64_json")
