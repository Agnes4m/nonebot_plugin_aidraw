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
draw_api_url = ""                      # 自定义 API 地址（留空用默认）
draw_model = "gpt-image-2"              # 模型名称
draw_default_size = "1024x1024"        # 图片尺寸
draw_proxy = ""                         # HTTP 代理，如 http://127.0.0.1:10808
```

> `draw_api_url` 和 `draw_backend` 至少设置其一
> - `openai` → `https://api.openai.com/v1/images/generations`
> - `gemini` → `https://generativelanguage.googleapis.com/v1beta/images/generations`
> - `sd` → `http://localhost:7860/sdapi/v1/txt2img`

### 使用

- `/绘图 一只可爱的小猫`
- 回复图片 + `/绘图 画成动漫风`（以图片为垫图）
- 回复消息 + `/绘图 ...`（从被回复消息中提取图片）

### 可选功能

```bash
draw_nsfw_enabled = true               # 启用 NSFW 关键词过滤（仅群聊）
draw_nsfw_keywords = ["敏感词1", "敏感词2"]
draw_whitelist_mode = true             # 白名单模式
draw_whitelist = ["group_123456"]      # 白名单 ID
draw_blacklist = ["group_654321"]       # 黑名单 ID
draw_quality = "standard"               # openai 图片质量
draw_n = 1                             # openai 生成数量
draw_response_format = "url"            # 返回格式 url / b64_json
```

## 功能

- 支持 OpenAI / Gemini / Stable Diffusion 多种后端
- 回复消息中的图片作为垫图
- NSFW 关键词过滤（仅群聊）
- 黑白名单访问控制
- b64_json 本地文件通过 base64:// 发送

## 协议

MIT © [@Agnes4m](https://github.com/Agnes4m)
