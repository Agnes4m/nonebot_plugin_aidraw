"""子包配置模块"""

from typing import Optional

from pydantic import BaseModel, Field


class EnvConfig(BaseModel):
    """插件配置类"""

    draw_api_url: str = Field(
        default="http://localhost:8080/v1/images/generations",
        description="绘图API地址",
    )
    draw_api_key: str = Field(
        default="",
        description="API密钥",
    )
    draw_model: str = Field(
        default="flux",
        description="使用的模型名称",
    )

    draw_default_size: str = Field(
        default="1024x1024",
        description="默认图片尺寸",
    )
    draw_timeout: int = Field(
        default=120,
        description="请求超时时间(秒)",
    )

    draw_nsfw_enabled: bool = Field(
        default=False,
        description="是否启用 NSFW 关键词检测",
    )
    draw_nsfw_keywords: list[str] = Field(
        default_factory=list,
        description="NSFW 关键词列表",
    )

    draw_trust_users: Optional[list[str]] = Field(
        default=None,
        description="信任用户ID列表，不为空时只有列表中的用户可以使用",
    )

    class Config:
        populate_by_name = True
