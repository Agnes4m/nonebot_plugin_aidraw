<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 MD051 -->
<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_easy_aidraw 0.1.0

_✨NoneBot & AI 绘图 插件 ✨_

<a href="https://github.com/Agnes4m/nonebot_plugin_easy_aidraw" target="_blank">仓库</a> &nbsp; · &nbsp;
<a href="https://github.com/Agnes4m/nonebot_plugin_easy_aidraw/issues" target="_blank">反馈</a>

<img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641" alt="python">
<img src="https://img.shields.io/badge/nonebot-2.4.0+-red.svg" alt="NoneBot">
<a href="https://pypi.python.org/pypi/nonebot-plugin-easy-aidraw">
<img src="https://img.shields.io/pypi/v/nonebot-plugin-easy-aidraw?logo=python&logoColor=edb641" alt="pypi">
</a>
<a href="https://github.com/Agnes4m/nonebot_plugin_easy_aidraw/issues">
<img alt="GitHub issues" src="https://img.shields.io/github/issues/Agnes4m/nonebot_plugin_easy_aidraw" alt="issues">
</a>
<a href="https://jq.qq.com/?_wv=1027&k=HdjoCcAe">
<img src="https://img.shields.io/badge/QQ%E7%BE%A4-399365126-orange?style=flat-square" alt="QQ Chat Group">
</a>
</div>

## 快速开始

### 安装

```bash
nb plugin install nonebot-plugin-easy-aidraw
```

### 配置

```bash
# .env 文件
draw_api_key = "your-api-key"          # API 密钥
draw_backend = "openai"                # openai / gemini / sd
draw_api_url = ""                      # 自定义 API 地址（留空用默认），必须以 http:// 或 https:// 开头
draw_model = "gpt-image-2"             # 模型名称
draw_default_size = "1024x1024"        # 图片尺寸
draw_proxy = ""                        # HTTP 代理，如 http://127.0.0.1:10808
```

> `draw_api_url` 和 `draw_backend` 至少设置其一
> - `openai` → `https://api.openai.com/v1/images/generations`
> - `gemini` → `https://generativelanguage.googleapis.com/v1beta/images/generations`
> - `sd` → `http://localhost:7860/sdapi/v1/txt2img`

### 使用

- `/绘图 一只可爱的小猫`
- `/绘图 --model gpt-image-1.5 --size 1024x1792 风景`
- `/绘图 --n 2 同一提示词生成两张`
- 回复图片 + `/绘图 画成动漫风`（以图片为垫图）
- 回复消息 + `/绘图 ...`（从被回复消息中提取图片）

### 可选功能

```bash
draw_user_cooldown = 60                # 单用户冷却时间（秒），0 禁用
draw_nsfw_enabled = true               # 启用 NSFW 关键词过滤（仅群聊）
draw_nsfw_keywords = ["敏感词1", "敏感词2"]
draw_whitelist_mode = true             # 白名单模式
draw_whitelist = ["123456"]            # 白名单用户 ID（QQ 号），对群/私聊统一生效
draw_blacklist = ["654321"]            # 黑名单用户 ID
draw_quality = "standard"              # openai 图片质量
draw_n = 1                             # openai 生成数量
draw_response_format = "url"           # 返回格式 url / b64_json
draw_cache_enabled = false             # 是否将 b64 图片落盘缓存（默认关闭）
draw_cache_dir = "data/nonebot_plugin_easy_aidraw"  # 缓存目录
draw_cache_ttl = 86400                 # 缓存过期时间（秒），用于 /清理绘图缓存
```

### 超级用户指令

```bash
/清理绘图缓存
```

清理超过 `draw_cache_ttl` 秒的缓存图片（按 mtime 判断）。仅在 `draw_cache_enabled=true` 时生效。

## 功能

- 支持 OpenAI / Gemini / Stable Diffusion 多种后端
- **请求队列**：单用户串行处理，前方有 N 个请求时显示排队位置
- **用户冷却**：单用户 N 秒内只能请求一次（可配置，超级用户无视）
- 回复消息中的图片作为垫图
- NSFW 关键词过滤（仅群聊）
- 黑白名单访问控制（按用户 ID，全局生效）
- URL / base64 两种返回格式（OneBot V11 走 base64:// 发送）
- 可选图片缓存与一键清理
- 子选项：`--model` / `--size` / `--n` 覆盖全局配置
- 发送图片后输出本次 token 用量与模型

## 协议

MIT © [@Agnes4m](https://github.com/Agnes4m)
