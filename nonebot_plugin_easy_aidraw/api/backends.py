"""后端默认端点与 URL 解析。"""

from __future__ import annotations

from dataclasses import dataclass

BACKEND_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {
        "base": "https://api.openai.com/v1",
        "txt2img": "/images/generations",
        "img2img": "/images/edits",
        "default_model": "gpt-image-2",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta",
        "txt2img": "/images/generations",
        "img2img": "/images/edits",
        "default_model": "gemini-pro",
    },
    "sd": {
        "base": "http://localhost:7860/sdapi/v1",
        "txt2img": "/txt2img",
        "img2img": "/img2img",
        "default_model": "sd15",
    },
}

KEY_NEEDED_BACKENDS = frozenset({"openai", "gemini"})

_OPENAI_SUFFIX = {"txt2img": "/images/generations", "img2img": "/images/edits"}


@dataclass(frozen=True)
class Endpoints:
    txt2img: str
    img2img: str
    backend: str


def _normalize_base(url: str) -> str:
    url = url.rstrip("/")
    for suffix in _OPENAI_SUFFIX.values():
        if url.endswith(suffix):
            return url[: -len(suffix)]
    return url


def _resolve_endpoint(raw_url: str, backend: str, suffix: str) -> str:
    if raw_url:
        if not raw_url.startswith(("http://", "https://")):
            raise ValueError("draw_api_url 必须以 http:// 或 https:// 开头")
        base = _normalize_base(raw_url.rstrip("/"))
        if not base.endswith("/v1"):
            raise ValueError("draw_api_url 必须以 /v1 结尾")
        return f"{base}{suffix}"
    defaults = BACKEND_DEFAULTS.get(backend)
    if defaults:
        return defaults["base"] + suffix
    raise ValueError("draw_api_url 或 draw_backend 必须设置其一")


def get_endpoint(backend: str, url: str, kind: str) -> str:
    defaults = BACKEND_DEFAULTS.get(backend)
    suffix = defaults.get(kind) if defaults else _OPENAI_SUFFIX.get(kind, f"/images/{kind}")
    return _resolve_endpoint(url, backend, suffix)


def resolve_edit_url(backend: str, txt2img_url: str, edits_url: str) -> str:
    if edits_url:
        return _resolve_endpoint(edits_url, backend, BACKEND_DEFAULTS.get(backend, {}).get("img2img", "/images/edits"))
    defaults = BACKEND_DEFAULTS.get(backend)
    if defaults:
        return defaults["base"] + defaults["img2img"]
    return txt2img_url.replace("/images/generations", "/images/edits")


def needs_api_key(backend: str) -> bool:
    return backend in KEY_NEEDED_BACKENDS
