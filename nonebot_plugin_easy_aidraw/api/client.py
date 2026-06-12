"""HTTP 客户端：OpenAI 协议文生图 / 图生图。"""

from __future__ import annotations

import base64
from pathlib import Path

import httpx
from nonebot.log import logger

from ..models import ImageData, ImageResponse, Usage
from .cache import b64_to_path
from .config_loader import get_config, needs_api_key
from .errors import sanitize_error

__all__ = ["edit_image", "generate_image"]


def _client_kwargs(cfg: dict) -> dict:
    kw: dict = {"timeout": cfg["timeout"]}
    proxy = cfg.get("proxy")
    if proxy:
        kw["proxy"] = proxy
    return kw


def _safe_headers(headers: dict) -> dict:
    return {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()}


def _sanitize_for_log(obj):
    if isinstance(obj, dict):
        return {k: ("<bytes>" if k in ("b64_json",) else _sanitize_for_log(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_log(i) for i in obj]
    return obj


def _build_usage(resp: ImageResponse, default_model: str) -> dict:
    usage = resp.usage or Usage()
    return {
        "model": resp.model or default_model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
    }


def _json_payload(cfg: dict, prompt: str) -> dict:
    payload: dict = {"model": cfg["model"], "prompt": prompt, "size": cfg["default_size"]}
    if cfg["backend"] == "openai":
        payload["n"] = cfg.get("n") or 1
        payload["quality"] = cfg.get("quality") or "standard"
    return payload


def _extract_all(resp: ImageResponse) -> list[ImageData]:
    if not resp.data:
        safe = resp.model_dump(exclude={"usage"}, exclude_none=True)
        raise ValueError(f"API 返回格式异常: {safe}")
    return resp.data


def _results_from(resp: ImageResponse) -> list[str | Path]:
    results: list[str | Path] = []
    for img in _extract_all(resp):
        if img.b64_json:
            p, _ = b64_to_path(img.b64_json)
            results.append(p)
        elif img.url:
            results.append(img.url)
    if not results:
        raise ValueError("API 未返回图片 URL 或 b64_json")
    return results


async def _post_json(client: httpx.AsyncClient, url: str, headers: dict, payload: dict) -> ImageResponse:
    logger.debug(f"[绘图] 请求体: {payload}")
    logger.debug(f"[绘图] headers: {_safe_headers(headers)}")
    try:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        body = (e.response.text or "").strip()
        logger.warning(f"[绘图] 上游错误 {e.response.status_code}: {body}")
        raise RuntimeError(sanitize_error(e.response.status_code, body)) from e
    resp = ImageResponse.model_validate(response.json())
    logger.info(f"[绘图] 响应: {_sanitize_for_log(resp.model_dump(exclude_none=True))}")
    return resp


def _require_key(backend: str, api_key: str) -> None:
    if needs_api_key(backend) and not api_key:
        raise ValueError("未配置 DRAW_API_KEY")


async def generate_image(prompt: str) -> tuple[list[str | Path], dict]:
    cfg = get_config()
    _require_key(cfg["backend"], cfg["api_key"])
    async with httpx.AsyncClient(**_client_kwargs(cfg)) as client:
        logger.info(f"[绘图] 请求: model={cfg['model']}, prompt_len={len(prompt)}, mode=txt2img")
        resp = await _post_json(client, cfg["api_url"], cfg["headers"], _json_payload(cfg, prompt))
    results = _results_from(resp)
    logger.info(f"[绘图] 生成成功: 共 {len(results)} 张")
    return results, _build_usage(resp, cfg["model"])


async def edit_image(prompt: str, image_b64: str) -> tuple[list[str | Path], dict]:
    cfg = get_config()
    _require_key(cfg["backend"], cfg["api_key"])

    form_data: dict = {"model": cfg["model"], "prompt": prompt, "n": str(cfg.get("n") or 1)}
    if cfg["backend"] == "openai":
        form_data["quality"] = cfg.get("quality") or "standard"

    files = {"image": ("image.png", base64.b64decode(image_b64), "image/png")}
    auth = cfg["headers"].get("Authorization")
    headers = {"Authorization": auth} if auth else {}

    async with httpx.AsyncClient(**_client_kwargs(cfg)) as client:
        logger.info(f"[绘图] 请求: model={cfg['model']}, prompt_len={len(prompt)}, mode=img2img")
        try:
            response = await client.post(cfg["api_url_edits"], headers=headers, data=form_data, files=files)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = (e.response.text or "").strip()
            logger.warning(f"[绘图] 上游错误 {e.response.status_code}: {body}")
            raise RuntimeError(sanitize_error(e.response.status_code, body)) from e
        resp = ImageResponse.model_validate(response.json())
        logger.info(f"[绘图] 响应: {_sanitize_for_log(resp.model_dump(exclude_none=True))}")

    results = _results_from(resp)
    logger.info(f"[绘图] 生成成功: 共 {len(results)} 张")
    return results, _build_usage(resp, cfg["model"])
