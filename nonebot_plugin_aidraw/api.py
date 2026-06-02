"""绘图 API 调用与配置访问"""

from __future__ import annotations

import re
from typing import Optional

import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger

_config: "Optional[dict]" = None


def _get_config() -> dict:
    """延迟获取配置"""
    global _config
    if _config is None:
        config_dict = dict(get_driver().config)
        _config = {
            "api_url": config_dict.get(
                "draw_api_url", "http://localhost:8080/v1/images/generations"
            ),
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


def check_nsfw(prompt: str) -> tuple[bool, Optional[str]]:
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


async def generate_image(prompt: str) -> Optional[str]:
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

    async with httpx.AsyncClient(timeout=config["timeout"]) as client:
        try:
            logger.debug(f"[绘图] API请求: {config['api_url']}")
            response = await client.post(
                config["api_url"],
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"[绘图] API返回: {data}")

            if "data" in data and len(data["data"]) > 0:
                img_data = data["data"][0]

                if img_data.get("url"):
                    return img_data["url"]
                raise ValueError("API未返回图片URL")
            raise ValueError(f"API返回格式异常: {data}")

        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP请求失败: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ValueError(f"请求异常: {e}") from e
