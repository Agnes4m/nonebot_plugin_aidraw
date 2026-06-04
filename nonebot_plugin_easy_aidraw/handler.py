"""命令注册与业务处理"""

import asyncio
import base64
from pathlib import Path
import time

from arclet.alconna import Alconna, CommandMeta
import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger
from nonebot_plugin_alconna import Image, UniMessage, UniMsg, on_alconna

from .api import _get_config, check_nsfw, check_whitelist_blacklist, generate_image, is_private_message

draw_alc = Alconna(
    "绘图",
    meta=CommandMeta(description="AI绘图命令", example="/绘图 一只可爱的小猫"),
)

draw_command = on_alconna(
    draw_alc, auto_send_output=False, use_origin=False, skip_for_unmatch=False, response_self=True
)

_draw_lock = asyncio.Lock()
_pending = 0
_user_last_request: dict[str, float] = {}


def _to_data_uri(data: bytes) -> str:
    return f"base64://{base64.b64encode(data).decode()}"


async def _send_image(result: str | Path) -> None:
    if isinstance(result, Path):
        await UniMessage.image(url=_to_data_uri(result.read_bytes())).send()
        return
    try:
        await UniMessage.image(url=result).send()
    except Exception as e:
        logger.warning(f"[绘图] URL 发送失败，回退下载: {e}")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(result)
            resp.raise_for_status()
        await UniMessage.image(url=_to_data_uri(resp.content)).send()


def _check_cooldown(user_id: str, cooldown_min: int) -> tuple[bool, int]:
    """检查用户冷却，返回 (是否通过, 剩余秒数)"""
    if cooldown_min <= 0:
        return True, 0
    last = _user_last_request.get(user_id)
    if last is None:
        return True, 0
    elapsed = time.time() - last
    remain = cooldown_min * 60 - int(elapsed)
    return (True, 0) if remain <= 0 else (False, remain)


@draw_command.handle()
async def handle_draw(event: Event, unimsg: UniMsg):
    global _pending
    if not (passed := check_whitelist_blacklist(event))[0]:
        return await UniMessage.text(f"❌ 访问被拒绝：{passed[1]}").finish()

    prompt = unimsg.extract_plain_text().strip()
    for prefix in ("/绘图", "绘图", "/画", "画"):
        if prompt.startswith(prefix):
            prompt = prompt[len(prefix) :].strip()
            break

    cfg = _get_config()
    user_id = event.get_user_id()
    cooldown_min = cfg.get("user_cooldown", 30)
    model_name = cfg.get("model", "unknown")

    superusers = set(get_driver().config.superusers)
    is_superuser = user_id in superusers

    if not is_superuser:
        ok, remain = _check_cooldown(user_id, cooldown_min)
        if not ok:
            mins, secs = divmod(remain, 60)
            return await UniMessage.text(f"⏳ 冷却中，还需等待 {mins}分{secs}秒").finish()

    if not is_private_message(event):
        is_nsfw, keyword = check_nsfw(prompt)
        if is_nsfw:
            return await UniMessage.text(f"❌ 检测到敏感词「{keyword}」").finish()

    if not prompt:
        return await UniMessage.text("❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫").finish()

    _pending += 1
    if _pending > 1:
        msg = f"🎨 正在使用 {model_name} 生成中（前面还有 {_pending - 1} 个请求）..."
    else:
        msg = f"🎨 正在使用 {model_name} 生成中..."
    await UniMessage.text(msg).send()

    result: str | Path = ""
    error_msg = ""
    try:
        async with _draw_lock:
            _user_last_request[user_id] = time.time()
            image_urls: list[str] = []
            if event.reply:
                for seg in event.reply.message:
                    if seg.type == "image" and seg.data.get("url"):
                        image_urls.append(seg.data["url"])
            image_urls.extend(img.data["url"] for img in unimsg[Image] if img.data.get("url"))
            logger.info(f"[绘图] 请求: prompt={prompt!r}, 图片={len(image_urls)}")
            result = await generate_image(prompt, image_urls or None)
    except Exception as e:
        logger.exception(f"[绘图] 生成失败: {e}")
        error_msg = str(e)
    finally:
        _pending -= 1

    if error_msg:
        return await UniMessage.text(f"❌ 生成失败: {error_msg}").finish()

    logger.info(f"[绘图] 生成成功: {result}")

    try:
        await _send_image(result)
    except Exception as e:
        logger.exception(f"[绘图] 发送失败: {e}")
        await UniMessage.text(f"❌ 发送失败: {result}").finish()
