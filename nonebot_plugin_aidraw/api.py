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


def _get_config() -> dict:
    """延迟获取配置"""
    global _config
    if _config is None:
        config_dict = dict(get_driver().config)
        api_url = config_dict.get("draw_api_url", "")
        backend = config_dict.get("draw_backend", "openai")
        base = BACKEND_BASES.get(backend, BACKEND_BASES["openai"])
        path = api_url if api_url else BACKEND_PATHS.get(backend, BACKEND_PATHS["openai"])
        full_url = base + path if not path.startswith("http") else path
        _config = {
            "api_url": full_url,
            "api_key": config_dict.get("draw_api_key", ""),
            "model": config_dict.get("draw_model", "flux"),
            "default_size": config_dict.get("draw_default_size", "1024x1024"),
            "timeout": config_dict.get("draw_timeout", 120),
            "nsfw_enabled": config_dict.get("draw_nsfw_enabled", False),
            "nsfw_keywords": config_dict.get("draw_nsfw_keywords", []),
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

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config["model"],
        "prompt": prompt,
        "n": 1,
        "size": config["default_size"],
    }

    if image_urls:
        payload["extra_body"] = {
            "image": image_urls,
            "response_format": "url",
        }

    async with httpx.AsyncClient(timeout=config["timeout"]) as client:
        logger.info(
            f"[绘图] 发起请求: url={config['api_url']}, "
            f"model={config['model']}, prompt_len={len(prompt)}, "
            f"size={config['default_size']}"
        )
        response = await client.post(config["api_url"], json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"[绘图] API返回: {data}")

        if "data" in data and len(data["data"]) > 0:
            img_data = data["data"][0]
            if url := img_data.get("url"):
                return url
            raise ValueError("API未返回图片URL")
        raise ValueError(f"API返回格式异常: {data}")
