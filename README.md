<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 MD051 -->
<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_aidraw 0.1.0

_✨Nonebot & AI 绘图 插件 ✨_

<div align = "center">
        <a href="https://github.com/Agnes4m/nonebot_plugin_aidraw" target="_blank">仓库</a> &nbsp; · &nbsp;
        <a href="https://github.com/Agnes4m/nonebot_plugin_aidraw/issues" target="_blank">指令 & 反馈</a> &nbsp; · &nbsp;
        <a href="https://github.com/Agnes4m/nonebot_plugin_aidraw/issues" target="_blank">常见问题</a>
</div><br>

<img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=edb641" alt="python">
<a href ="LICENSE">
<img src="https://img.shields.io/github/license/Agnes4m/nonebot_plugin_aidraw" alt="aidrawlogo">
</a>
<img src="https://img.shields.io/badge/nonebot-2.1.0+-red.svg" alt="NoneBot">
<a href="https://pypi.python.org/pypi/nonebot-plugin-aidraw">
<img src="https://img.shields.io/pypi/v/nonebot-plugin-aidraw?logo=python&logoColor=edb641" alt="python">
</a>
</br>
<a href="https://github.com/astral-sh/ruff">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
</a>
<a href="https://github.com/psf/black">
<img src="https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&logoColor=edb641" alt="black">
</a>

<img src="https://img.shields.io/badge/alconna-0.50.0+-red.svg" alt="NoneBot">

<a href="https://github.com/Agnes4m/nonebot_plugin_aidraw/issues">
        <img alt="GitHub issues" src="https://img.shields.io/github/issues/Agnes4m/nonebot_plugin_aidraw" alt="issues">
</a>

<a href="https://pypi.python.org/pypi/nonebot-plugin-aidraw">
    <img src="https://img.shields.io/pypi/dm/nonebot-plugin-aidraw" alt="pypi download">
</a>
</br>
<a href="https://jq.qq.com/?_wv=1027&k=HdjoCcAe">
        <img src="https://img.shields.io/badge/QQ%E7%BE%A4-399365126-orange?style=flat-square" alt="QQ Chat Group">
</a>
</div>

## 快速使用


### 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-aidraw
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-aidraw
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-aidraw
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-aidraw
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-aidraw
```

</details>
<details>
<summary>uv</summary>

```bash
uv install nonebot-plugin-aidraw
```

</details>
</details>

### env最简化配置

draw_api_url = "http://localhost:8080"      # API 地址
draw_api_key = ""                           # API 密钥
draw_model = "gpt-image-2"                  # 模型名称

## 功能

- `绘图` 调用绘图 API 生成图片

### 支持的绘图后端

- 任意 OpenAI 兼容的 `/v1/images/generations` 接口（如 OpenAI、Gemini、本地自部署等）
- 返回 `url` 时直接转发图片链接
- 自定义 API 地址、密钥、模型、尺寸、超时

### NSFW 过滤

- 群聊场景下可选启用 NSFW 关键词过滤（`DRAW_NSFW_ENABLED=true` + `DRAW_NSFW_KEYWORDS=[...]`）
- 私聊自动跳过检测

### 输出容错

- 一旦拿到图片 URL，即使后续发送环节出现小问题，也不会再向用户推送错误消息，避免误扰


## 主要功能

- [x] 调用 OpenAI 兼容绘图接口生成图片
- [x] 支持自定义 API 地址、密钥、模型
- [x] 支持 base64 / URL 两种返回格式
- [x] 群聊 NSFW 关键词过滤（可关闭）
- [x] 黑白名单访问控制（支持群组/用户 ID）

## env 设置

```bash
draw_api_url = "http://localhost:8080"      # API 地址
draw_api_key = ""                           # API 密钥
draw_model = "flux"                         # 模型名称
draw_backend = "openai"                     # 后端类型: openai/gemini/sd
draw_default_size = "1024x1024"            # 图片尺寸
draw_timeout = 120                          # 超时时间(秒)
draw_nsfw_enabled = false                  # NSFW 检测（仅群聊）
draw_nsfw_keywords = []                    # NSFW 关键词
draw_whitelist_mode = false                # 白名单模式
draw_whitelist = []                        # 白名单
draw_blacklist = []                         # 黑名单
```

> `draw_api_url` 留空时使用后端默认地址；填写时作为后缀拼接到 base URL 后面
> ID 格式：`group_123456`（群组）或 `123456`（私聊）

## 其他

- 如果您有发现 BUG 或者更好的建议，欢迎提 Issue & Pr
- 如果本插件对你有帮助，不要忘了点个 Star~
- 本项目仅供学习使用，请勿用于商业用途
- [MIT License](https://github.com/Agnes4m/nonebot_plugin_aidraw/blob/main/LICENSE) ©[@Agnes4m](https://github.com/Agnes4m)

## 🌐 感谢

- [nonebot2](https://github.com/nonebot/nonebot2) - 聊天机器人的基础框架
- [nonebot-plugin-alconna](https://github.com/nonebot-plugin-alconna/nonebot-plugin-alconna) - NoneBot2 的 Alconna 适配
