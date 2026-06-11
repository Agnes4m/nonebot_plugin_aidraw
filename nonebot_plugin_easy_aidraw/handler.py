"""命令注册与业务处理"""

import asyncio
import base64
from pathlib import Path
import time

from arclet.alconna import Alconna, Args, Arparma, CommandMeta, Option
import httpx
from nonebot import get_driver
from nonebot.adapters import Event
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import Image, UniMessage, UniMsg, on_alconna

from .api import _get_config, check_nsfw, check_whitelist_blacklist, cleanup_cache, generate_image, is_private_message

_DOWNLOAD_TIMEOUT = 60

draw_alc = Alconna(
    "绘图",
    Option("--model", Args["model", str], help_text="指定模型"),
    Option("--size", Args["size", str], help_text="指定图片尺寸，如 1024x1024"),
    Option("--n", Args["n", int], help_text="生成数量"),
    meta=CommandMeta(
        description="AI绘图命令",
        example="/绘图 一只可爱的小猫\n/绘图 --model gpt-image-1.5 --size 1024x1792 风景",
    ),
)

draw_command = on_alconna(
    draw_alc, auto_send_output=False, use_origin=False, skip_for_unmatch=False, response_self=True
)

clear_cache_alc = Alconna(
    "清理绘图缓存",
    meta=CommandMeta(description="清理过期绘图缓存（SUPERUSER）", example="/清理绘图缓存"),
)
clear_cache_command = on_alconna(clear_cache_alc, auto_send_output=False, permission=SUPERUSER)

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
        logger.warning(f"[绘图] URL 发送失败，回退下载转 base64: {e}")
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT) as client:
            resp = await client.get(result)
            resp.raise_for_status()
            data = resp.content
        await UniMessage.image(url=_to_data_uri(data)).send()


def _check_cooldown(user_id: str, cooldown_sec: int) -> tuple[bool, int]:
    if cooldown_sec <= 0:
        return True, 0
    last = _user_last_request.get(user_id)
    if last is None:
        return True, 0
    elapsed = time.time() - last
    remain = cooldown_sec - int(elapsed)
    return (True, 0) if remain <= 0 else (False, remain)


@draw_command.handle()
async def handle_draw(event: Event, arp: Arparma, unimsg: UniMsg):
    global _pending
    if not (passed := check_whitelist_blacklist(event))[0]:
        return await UniMessage.text(f"❌ 访问被拒绝：{passed[1]}").finish()

    prompt = unimsg.extract_plain_text().strip()

    cfg = _get_config()
    user_id = event.get_user_id()
    cooldown_sec = cfg.get("user_cooldown", 60)

    superusers = set(get_driver().config.superusers)
    is_superuser = user_id in superusers

    if not is_superuser:
        ok, remain = _check_cooldown(user_id, cooldown_sec)
        if not ok:
            mins, secs = divmod(remain, 60)
            return await UniMessage.text(f"⏳ 冷却中，还需等待 {mins}分{secs}秒").finish()

    if not is_private_message(event):
        is_nsfw, keyword = check_nsfw(prompt)
        if is_nsfw:
            return await UniMessage.text(f"❌ 检测到敏感词「{keyword}」").finish()

    if not prompt:
        return await UniMessage.text("❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫").finish()

    model_override = None
    size_override = None
    n_override = None
    try:
        for opt in arp.options:
            name = opt.name if hasattr(opt, "name") else None
            if name == "model":
                model_override = opt.value.get("model") if hasattr(opt, "value") else None
            elif name == "size":
                size_override = opt.value.get("size") if hasattr(opt, "value") else None
            elif name == "n":
                n_override = opt.value.get("n") if hasattr(opt, "value") else None
    except Exception:
        pass

    used_model = model_override or cfg.get("model", "unknown")
    used_size = size_override or cfg.get("default_size", "1024x1024")

    _pending += 1
    pending_snapshot = _pending
    if pending_snapshot > 1:
        msg = f"🎨 正在使用 {used_model} 生成中（前面还有 {pending_snapshot - 1} 个请求）..."
    else:
        msg = f"🎨 正在使用 {used_model} 生成中..."
    await UniMessage.text(msg).send()

    result: str | Path | None = None
    usage_info = None
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
            logger.info(f"[绘图] 请求: prompt={prompt!r}, model={used_model}, size={used_size}, 图片={len(image_urls)}")

            from .api import _get_config as _g

            c = _g()
            if size_override:
                c["default_size"] = size_override
            if n_override:
                c["n"] = n_override
            if model_override:
                c["model"] = model_override

            result, usage_info = await generate_image(prompt, image_urls or None)
    except Exception as e:
        logger.exception(f"[绘图] 生成失败: {e}")
        error_msg = str(e)
    finally:
        _pending -= 1

    if error_msg:
        return await UniMessage.text(f"❌ 生成失败: {error_msg}").finish()

    try:
        await _send_image(result)
        if usage_info and any(v for v in (usage_info.input_tokens, usage_info.output_tokens, usage_info.total_tokens)):
            await UniMessage.text(f"📊 本次消耗: {usage_info.format()}").send()
    except Exception as e:
        logger.exception(f"[绘图] 发送失败: {e}")
        await UniMessage.text(f"❌ 发送失败: {result}").finish()
    finally:
        if isinstance(result, Path) and not cfg.get("cache_enabled", False):
            try:
                result.unlink(missing_ok=True)
            except OSError:
                pass


@clear_cache_command.handle()
async def handle_clear_cache():
    cfg = _get_config()
    if not cfg.get("cache_enabled", False):
        return await UniMessage.text("ℹ️ 缓存功能未启用（draw_cache_enabled=False），无需清理").finish()
    deleted, remaining = cleanup_cache()
    return await UniMessage.text(f"🧹 清理完成：删除 {deleted} 个，剩余 {remaining} 个").finish()
