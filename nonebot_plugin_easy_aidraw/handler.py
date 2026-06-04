"""命令注册与业务处理"""

import base64
from pathlib import Path

from arclet.alconna import Alconna, CommandMeta
import httpx
from nonebot.adapters import Event
from nonebot.log import logger
from nonebot_plugin_alconna import Image, UniMessage, UniMsg, on_alconna

from .api import check_nsfw, check_whitelist_blacklist, generate_image, is_private_message

draw_alc = Alconna(
    "绘图",
    meta=CommandMeta(description="AI绘图命令", example="/绘图 一只可爱的小猫"),
)

draw_command = on_alconna(
    draw_alc, auto_send_output=False, use_origin=False, skip_for_unmatch=False, response_self=True
)


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


@draw_command.handle()
async def handle_draw(event: Event, unimsg: UniMsg):
    if not (passed := check_whitelist_blacklist(event))[0]:
        return await UniMessage.text(f"❌ 访问被拒绝：{passed[1]}").finish()

    prompt = unimsg.extract_plain_text().strip()
    for prefix in ("/绘图", "绘图", "/画", "画"):
        if prompt.startswith(prefix):
            prompt = prompt[len(prefix) :].strip()
            break

    image_urls: list[str] = []

    if event.reply:
        for seg in event.reply.message:
            if seg.type == "image" and seg.data.get("url"):
                image_urls.append(seg.data["url"])

    image_urls.extend(img.data["url"] for img in unimsg[Image] if img.data.get("url"))

    logger.info(f"[绘图] 请求: prompt={prompt!r}, 图片={len(image_urls)}")

    if not is_private_message(event):
        is_nsfw, keyword = check_nsfw(prompt)
        if is_nsfw:
            return await UniMessage.text(f"❌ 检测到敏感词「{keyword}」").finish()

    if not prompt:
        return await UniMessage.text("❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫").finish()

    await UniMessage.text("🎨 正在生成图片，请稍候...").send()

    try:
        result = await generate_image(prompt, image_urls or None)
    except Exception as e:
        logger.exception(f"[绘图] 生成失败: {e}")
        return await UniMessage.text(f"❌ 生成失败: {e}").finish()

    logger.info(f"[绘图] 生成成功: {result}")

    try:
        await _send_image(result)
    except Exception as e:
        logger.exception(f"[绘图] 发送失败: {e}")
        await UniMessage.text(f"❌ 发送失败: {result}").finish()
