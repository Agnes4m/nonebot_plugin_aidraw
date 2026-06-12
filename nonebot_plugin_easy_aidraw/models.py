"""API 响应模型"""

from pydantic import BaseModel, ConfigDict, Field


class ImageData(BaseModel):
    b64_json: str | None = None
    url: str | None = None
    revised_prompt: str | None = None


class Usage(BaseModel):
    input_tokens: int | None = None
    input_tokens_details: dict | None = None
    output_tokens: int | None = None
    output_tokens_details: dict | None = None
    total_tokens: int | None = None


class ImageResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    created: int | None = None
    data: list[ImageData] = Field(default_factory=list)
    background: str | None = None
    output_format: str | None = None
    quality: str | None = None
    size: str | None = None
    model: str | None = None
    usage: Usage | None = None
    error: dict | None = None
