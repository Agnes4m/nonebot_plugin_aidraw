<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 MD051 -->
<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_easy_aidraw 0.1.1

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

## 介绍

  本插件用于快速使用openai格式图像模型，兼容各种中转站或者其他openai兼容格式，只需要填写url/key/model三个参数即可快速使用

### 示例

![](./img/test1.png)


## 快速开始

### 安装

```bash
nb plugin install nonebot-plugin-easy-aidraw
```

### 最小配置（仅 3 个参数即可使用）

只需要 `draw_api_url` / `draw_api_key` / `draw_model`，其余全部走默认值：

```bash
# .env 文件
draw_api_url = "https://api.openai.com/v1"   # 自定义中转站 base URL，必须以 /v1 类似结尾
draw_api_key = "your-api-key"                     # API 密钥
draw_model = "gpt-image-2"              # 模型名称
```

- `draw_api_url` 留空时按 `draw_backend` 走官方默认（`openai` / `gemini` / `sd`）都不填写默认为`openai`。
- 填写时必须以 `/v1` 结尾，例如 `https://api.openai.com/v1`（插件会自动拼接 `/images/generations`）。若填写了 `/v1/images/generations` 也会被自动截断为 base URL。
- 文生图与图生图共用同一个 base URL，结尾分别追加 `/images/generations` 与 `/images/edits`。

### 使用

- `/绘图 一只可爱的小猫`
- `/绘图 --model gpt-image-2 --size 1024x1792 风景`
- `/绘图 --n 2 同一提示词生成两张`
- 回复图片 + `/绘图 画成动漫风`（以图片为垫图，走 `/images/edits`）
- 回复消息 + `/绘图 ...`（从被回复消息中提取图片）

## 完整参数配置

在最小配置基础上，下列参数全部可选，按需启用。

### 后端选择

```bash
draw_backend = "openai"   # openai / gemini / sd
```

各后端默认端点：

| 后端 | 文生图 | 图生图 |
|------|--------|--------|
| `openai` | `https://api.openai.com/v1/images/generations` | `https://api.openai.com/v1/images/edits` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/images/generations` | `https://generativelanguage.googleapis.com/v1beta/images/edits` |
| `sd` | `http://localhost:7860/sdapi/v1/txt2img` | `http://localhost:7860/sdapi/v1/img2img` |

### 端点覆盖

```bash
draw_api_url = "https://api.openai.com/v1"   # 文生图 base URL（必填其一或 draw_backend）
draw_api_url_edits = ""                          # 图生图 base URL（留空则与 draw_api_url 共享）
```

> 图生图采用 OpenAI 官方 `multipart/form-data` 规范（`image` 文件 + `prompt` + 其他表单字段），兼容中转站。

### 请求参数

```bash
draw_default_size = "1024x1024"   # 默认图片尺寸
draw_quality = "standard"         # openai 图片质量
draw_n = 1                        # openai 生成数量
draw_timeout = 120                # 请求超时（秒）
draw_proxy = ""                   # HTTP 代理，如 http://127.0.0.1:10808
```

### 访问控制

```bash
draw_user_cooldown = 60           # 单用户冷却时间（秒），0 禁用，超级用户无视
draw_concurrent = false           # 是否允许并发请求；false（默认）=前一个请求完成才继续下一个
draw_nsfw_enabled = false         # 启用 NSFW 关键词过滤（仅群聊）
draw_nsfw_keywords = []           # 敏感词列表
draw_whitelist_mode = false       # 白名单模式（true 启用白名单，false 走黑名单）
draw_whitelist = []               # 白名单用户 ID（QQ 号），对群/私聊统一生效
draw_blacklist = []               # 黑名单用户 ID
```

### 图片缓存

```bash
draw_cache_enabled = false        # 是否将 b64 图片落盘缓存（默认关闭）
draw_cache_dir = "data/nonebot_plugin_easy_aidraw"  # 缓存目录
draw_cache_ttl = 86400            # 缓存过期时间（秒）
```

### 超级用户指令

```bash
/清理绘图缓存
```

清理超过 `draw_cache_ttl` 秒的缓存图片（按 mtime 判断）。仅在 `draw_cache_enabled=true` 时生效。

## 功能

- 支持 OpenAI / Gemini / Stable Diffusion 多种后端
- **请求队列**：默认前一个请求完成才继续下一个；`draw_concurrent=true` 时允许并发
- **用户冷却**：单用户 N 秒内只能请求一次（可配置，超级用户无视）
- **图生图**：回复图片时自动走 `/images/edits`（OpenAI 官方 multipart/form-data），文生图与图生图端点可独立配置
- NSFW 关键词过滤（仅群聊）
- 黑白名单访问控制（按用户 ID，全局生效）
- URL / base64 两种返回格式（URL 发送失败自动回退下载转 base64 重发）
- 可选图片缓存与一键清理
- 子选项：`--model` / `--size` / `--n` 覆盖全局配置
- 发送图片后输出耗时与中文 token 用量（`⏱️ 耗时 X 秒 | 📊 消耗 输入 N、输出 M tokens`，token 为 0 时只输出耗时）

## 协议

MIT © [@Agnes4m](https://github.com/Agnes4m)
