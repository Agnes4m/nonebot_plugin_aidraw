"""nonebot_plugin_easy_aidraw - AI绘图插件"""

__version__ = "0.2.1"

from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from .config import EnvConfig
from .handler import clear_cache_command, draw_command

require("nonebot_plugin_alconna")

__plugin_meta__ = PluginMetadata(
    name="AI绘图",
    description="AI绘图插件，支持调用本地或远程的绘图API生成图片",
    usage=(
        "使用 /绘图 <提示词> 生成图片\n"
        "例如: /绘图 一只可爱的小猫\n"
        "可选参数: --model <模型> --size <尺寸> --n <数量>\n"
        "例如: /绘图 --model gpt-image-1.5 --size 1024x1792 风景\n"
        "超级用户: /清理绘图缓存 清理过期缓存"
    ),
    type="application",
    homepage="https://github.com/Agnes4m/nonebot_plugin_easy_aidraw",
    config=EnvConfig,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={"version": __version__, "author": "Agnes4m"},
)

__all__ = ["EnvConfig", "__plugin_meta__", "clear_cache_command", "draw_command"]
