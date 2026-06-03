"""命令注册与业务处理"""

from __future__ import annotations

from arclet.alconna import Alconna, CommandMeta
from nonebot.adapters import Event
from nonebot.log import logger
from nonebot_plugin_alconna import Image, UniMessage, UniMsg, on_alconna

from .api import check_nsfw, check_whitelist_blacklist, generate_image, is_private_message

draw_alc = Alconna(
    "绘图",
    meta=CommandMeta(description="AI绘图命令", example="/绘图 一只可爱的小猫"),
)

draw_command = on_alconna(draw_alc, auto_send_output=False, use_origin=True, skip_for_unmatch=False)


@draw_command.handle()
async def handle_draw(event: Event, unimsg: UniMsg):
    if not (passed := check_whitelist_blacklist(event))[0]:
        return await UniMessage.text(f"❌ 访问被拒绝：{passed[1]}").finish()

    prompt = unimsg.extract_plain_text().strip()
    for prefix in ["/绘图", "绘图", "/画", "画"]:
        if prompt.startswith(prefix):
            prompt = prompt[len(prefix) :].strip()
            break

    image_urls = [img.data["url"] for img in unimsg[Image] if img.data.get("url")]

    logger.info(f"[绘图] 用户请求绘图: {prompt}, 附带图片: {len(image_urls)}")

    if not is_private_message(event):
        is_nsfw, keyword = check_nsfw(prompt)
        if is_nsfw:
            logger.warning(f"[绘图] 检测到敏感词: {keyword}")
            return await UniMessage.text(f"❌ 检测到敏感词「{keyword}」，请修改提示词").finish()

    if not prompt:
        return await UniMessage.text("❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫").finish()
    await UniMessage.text("🎨 正在生成图片，请稍候...").send()

    image_url = await generate_image(prompt, image_urls or None)

    if not image_url:
        return await UniMessage.text("❌ 图片生成失败").finish()
    logger.info(f"[绘图] 图片生成成功: {image_url}")
    try:
        if image_url.startswith("/"):
            await UniMessage.image(path=image_url).send()
        else:
            await UniMessage.image(url=image_url).send()
    except Exception as e:
        logger.error(f"[绘图] 发送失败: {e}")
        await UniMessage.text(f"❌ 发送失败，可手动访问: {image_url}").finish()
