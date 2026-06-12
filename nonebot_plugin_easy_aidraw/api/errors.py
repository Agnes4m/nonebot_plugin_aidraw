"""错误信息脱敏：白名单用户提示，其余统一文案。"""

from __future__ import annotations

from json import JSONDecodeError, JSONDecoder

__all__ = ["sanitize_error"]

_USER_FRIENDLY = {
    "insufficient_quota": "💰 账户余额不足，请联系管理员充值",
    "invalid_api_key": "🔑 API Key 无效，请联系管理员检查配置",
    "rate_limit_exceeded": "🐢 触发上游限流，请稍后再试",
    "billing_hard_limit_reached": "💰 已达账单上限，请联系管理员",
    "content_policy_violation": "🚫 提示词违反内容策略，请调整后重试",
}
_decoder = JSONDecoder()


def _try_json(text: str) -> dict | None:
    if not text:
        return None
    try:
        data = _decoder.decode(text)
    except JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def sanitize_error(status: int, body: str) -> str:
    if status in (401, 403):
        return "🔑 鉴权失败，请联系管理员检查 API Key"
    if status == 429:
        return "🐢 请求过于频繁，请稍后再试"
    if status in (400, 422):
        payload = _try_json(body) or {}
        err = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        code = (err or {}).get("code") or payload.get("code") or ""
        if code in _USER_FRIENDLY:
            return _USER_FRIENDLY[code]
        if code:
            return f"❌ 请求被拒绝：{code}"
    if 500 <= status < 600:
        return f"💥 上游服务异常 ({status})，请稍后重试"
    return f"❌ 调用失败 ({status})"
