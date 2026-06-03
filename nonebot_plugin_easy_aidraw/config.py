"""子包配置模块"""

from pydantic import BaseModel


class EnvConfig(BaseModel):
    draw_api_url: str = "http://localhost:8080"
    draw_api_key: str = ""
    draw_model: str = "flux"
    draw_backend: str = "openai"
    draw_default_size: str = "1024x1024"
    draw_timeout: int = 120
    draw_nsfw_enabled: bool = False
    draw_nsfw_keywords: list[str] = []
    draw_whitelist_mode: bool = False
    draw_whitelist: list[str] = []
    draw_blacklist: list[str] = []

    class Config:
        populate_by_name = True
