"""子包配置模块"""

from pydantic import BaseModel


class EnvConfig(BaseModel):
    draw_api_url: str = ""
    draw_api_url_edits: str = ""
    draw_api_key: str = ""
    draw_model: str = ""
    draw_backend: str = ""
    draw_default_size: str = "1024x1024"
    draw_timeout: int = 120
    draw_proxy: str | None = None
    draw_nsfw_enabled: bool = False
    draw_nsfw_keywords: list[str] = []
    draw_whitelist_mode: bool = False
    draw_whitelist: list[str] = []
    draw_blacklist: list[str] = []
    draw_quality: str | None = None
    draw_n: int | None = None
    draw_user_cooldown: int = 60
    draw_concurrent: bool = False
    draw_cache_enabled: bool = False
    draw_cache_dir: str = "data/nonebot_plugin_easy_aidraw"
    draw_cache_ttl: int = 86400

    class Config:
        populate_by_name = True
