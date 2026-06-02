"""命令注册与业务处理"""

from __future__ import annotations

from nonebot.adapters import Event, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot_plugin_alconna import UniMessage

from .api import check_nsfw, generate_image, is_private_message

try:
    from arclet.alconna import Alconna, Args, CommandMeta
    from nonebot_plugin_alconna import on_alconna

    draw_alc = Alconna(
        "绘图",
        Args["prompt", str],
        meta=CommandMeta(description="AI绘图命令", example="/绘图 一只可爱的小猫"),
    )

    draw_command = on_alconna(draw_alc, auto_send_output=False)

    @draw_command.handle()
    async def handle_draw_alconna(event: Event):
        """处理绘图命令（alconna版本）"""
        msg = event.get_message()
        prompt = msg.extract_plain_text().strip()
        for prefix in ["/绘图", "绘图", "/画", "画"]:
            if prompt.startswith(prefix):
                prompt = prompt[len(prefix) :].strip()
                break

        logger.info(f"[绘图] 用户请求绘图: {prompt}")

        if not is_private_message(event):
            is_nsfw, keyword = check_nsfw(prompt)
            if is_nsfw:
                logger.warning(f"[绘图] 检测到敏感词: {keyword}")
                await UniMessage.text(
                    f"❌ 检测到敏感词「{keyword}」，请修改提示词"
                ).finish()
                return

        if not prompt:
            await UniMessage.text(
                "❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫"
            ).finish()
            return

        await UniMessage.text("🎨 正在生成图片，请稍候...").send()

        try:
            image_url = await generate_image(prompt)
        except Exception as e:
            logger.error(f"[绘图] 生成失败: {e}")
            await UniMessage.text(f"❌ 生成失败: {e}").finish()
            return

        if not image_url:
            await UniMessage.text("❌ 图片生成失败").finish()
            return

        try:
            await UniMessage.image(url=image_url).send()
            logger.info(f"[绘图] 图片发送成功: {image_url}")
        except Exception as e:
            logger.error(f"[绘图] 图片发送失败（URL={image_url}）: {e}")
        return


except ImportError:
    from nonebot import on_command

    draw_command = on_command("绘图", aliases={"绘画", "生成图片"}, priority=5)

    @draw_command.handle()
    async def handle_draw_fallback(event: Event, args: Message = CommandArg()):
        """处理绘图命令（回退版本）"""
        prompt = args.extract_plain_text().strip()

        logger.info(f"[绘图] 用户请求绘图: {prompt}")

        if not is_private_message(event):
            is_nsfw, keyword = check_nsfw(prompt)
            if is_nsfw:
                logger.warning(f"[绘图] 检测到敏感词: {keyword}")
                await draw_command.finish(f"❌ 检测到敏感词「{keyword}」，请修改提示词")
                return

        if not prompt:
            await draw_command.finish("❌ 请提供绘图提示词\n例如: /绘图 一只可爱的小猫")
            return

        await draw_command.send("🎨 正在生成图片，请稍候...")

        try:
            image_url = await generate_image(prompt)
        except Exception as e:
            logger.error(f"[绘图] 生成失败: {e}")
            await draw_command.finish(f"❌ 生成失败: {e}")
            return

        if not image_url:
            await draw_command.finish("❌ 图片生成失败")
            return

        try:
            await UniMessage.image(url=image_url).send()
            logger.info(f"[绘图] 图片发送成功: {image_url}")
        except Exception as e:
            logger.error(f"[绘图] 图片发送失败（URL={image_url}）: {e}")
        return
