# OpenAI 图像生成与编辑

[![Version](https://img.shields.io/github/v/release/XKPU/astrbot_plugin_openai_image?logo=github)](https://github.com/XKPU/astrbot_plugin_openai_image)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green?logo=data:image/svg+xml;base64,PHN2ZyB0PSIxNzg2ODczMTA1MjgwIiBjbGFzcz0iaWNvbiIgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHAtaWQ9IjY2MzEiIHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIj48cGF0aCBkPSJNNTEyIDE2QzIzOC4wNjYgMTYgMTYgMjM4LjA2NiAxNiA1MTJzMjIyLjA2NiA0OTYgNDk2IDQ5NiA0OTYtMjIyLjA2NiA0OTYtNDk2Uzc4NS45MzQgMTYgNTEyIDE2eiBtMCA4OTZjLTIyMS4wNjQgMC00MDAtMTc4LjkwMi00MDAtNDAwIDAtMjIxLjA2MiAxNzguOTAyLTQwMCA0MDAtNDAwIDIyMS4wNjQgMCA0MDAgMTc4LjkwMiA0MDAgNDAwIDAgMjIxLjA2NC0xNzguOTAyIDQwMC00MDAgNDAweiBtMjE0LjcwMi0yMDIuMTI4Yy0xOS4yMjggMTkuNDI0LTkxLjA2IDgyLjc5Mi0yMDguMTMgODIuNzkyLTE2NC44NiAwLTI4MC45NjgtMTIyLjg1LTI4MC45NjgtMjgzLjEzNCAwLTE1OC4zMDQgMTIwLjU1LTI3OC44MDIgMjc5LjUyNC0yNzguODAyIDExMS4wNjIgMCAxNzcuNDc2IDUzLjI0IDE5NS4xODYgNjkuNTU4YTIzLjkzIDIzLjkzIDAgMCAxIDMuODcyIDMwLjY0NGwtMzYuMzEgNTYuMjI2Yy03LjY4MiAxMS45LTIzLjkzMiAxNC41NjQtMzQuOTk4IDUuODQyLTE3LjE5LTEzLjU1Mi02My42MjgtNDUuMDc2LTEyMy40MTYtNDUuMDc2LTk2LjYwNiAwLTE1NS44MzIgNzAuNjYtMTU1LjgzMiAxNjAuMTY0IDAgODMuMTc4IDUzLjc3NiAxNjcuMzg0IDE1Ni41NTQgMTY3LjM4NCA2NS4zMTQgMCAxMDMuNjg2LTM4LjA3OCAxMzEuNDUyLTU0LjQ1IDEwLjU0LTkuNzE0IDI3LjE5Mi04LjA3OCAzNS42NCAzLjQ3NmwzOS43MyA1NC4zNGEyMy44OTQgMjMuODk0IDAgMCAxLTIuMzA0IDMxLjAzNnoiIGZpbGw9IiNmZmZmZmYiIHAtaWQ9IjY2MzIiPjwvcGF0aD48L3N2Zz4=)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-AstrBot-purple?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cGF0aCBkPSJNMzUgMjBRMzcgNDIgNjUgNTJRMzcgNjIgMzUgODRRMzMgNjIgNSA1MlEzMyA0MiAzNSAyMFoiIGZpbGw9IiM0Mjc4YjgiLz48cGF0aCBkPSJNNzUgMTJRNzYgMjMgODggMjdRNzYgMzEgNzUgNDJRNzQgMzEgNjIgMjdRNzQgMjMgNzUgMTJaIiBmaWxsPSIjNDI3OGI4Ii8+PC9zdmc+)](https://github.com/Soulter/AstrBot)
[![Author](https://custom-icon-badges.demolab.com/badge/author-K__PU-orange?logo=k_pu)](https://github.com/XKPU)

为 AstrBot 提供 OpenAI 兼容的图像生成与编辑能力。只要服务实现 `/v1/images/generations` 与 `/v1/images/edits`，即可接入本插件。

## 目录

- [工具](#工具)
- [配置](#配置)
  - [服务来源](#服务来源)
  - [全局配置](#全局配置)
  - [模型选择](#模型选择)
- [聊天命令](#聊天命令)
- [区域管理](#区域管理)
- [可视化配置](#可视化配置)
- [代码结构](#代码结构)
- [参考图下载](#参考图下载)
- [错误提示](#错误提示)
- [社区贡献者](#社区贡献者)
  - [代码贡献](#代码贡献)
- [许可证](#许可证)

## 工具

插件向 LLM 注册以下三个工具：

| 工具 | 功能 |
| --- | --- |
| `openai_image_generate` | 依据文本提示词生成图像 |
| `openai_image_edit` | 编辑附带或传入的一张或多张图像 |
| `openai_image_polish_prompt` | 将简短描述润色为详细的图像提示词（可关闭） |

## 配置

### 服务来源

通过 `sources` 列表配置多个服务来源，支持多密钥轮询与多模型回退。

| 字段 | 说明 |
| --- | --- |
| `name` | 来源名称，同时作为模型标签的前缀「来源名称/模型ID」 |
| `api_base` | 接口地址（含 `/v1`，如 `https://api.openai.com/v1`） |
| `models` | 模型列表，写法：`"模型ID"`、`"模型ID:重试次数"` 或 `{"id": ..., "retries": ...}` |
| `api_keys` | API 密钥列表，按顺序轮询 |
| `enable_generation` / `enable_edit` | 是否参与图像生成 / 图像编辑 |
| `aspect_ratios` | 可用宽高比 / 尺寸，留空沿用全局配置 |
| `aspect_ratio_field` | 宽高比写入字段，留空沿用全局配置（默认 `size`） |
| `validate_aspect_ratio` | 是否校验宽高比 / 尺寸取值，关闭后任意取值原样透传 |
| `response_image_path` | 响应图像路径，留空沿用全局配置（默认 `data`） |
| `generation_prompt` / `edit_prompt` | 附加提示词，留空沿用全局配置 |
| `extra_request_body` | 额外请求体字段，与全局配置合并，同名键以此处为准 |
| `timeout` | 请求超时（秒），`0` 表示沿用全局超时 |
| `enabled` | 是否启用该来源 |

请求顺序：按来源列表顺序、模型列表顺序依次尝试，每个密钥按「重试次数 + 1」次请求后切换下一项。

### 全局配置

| 配置项 | 说明 |
| --- | --- |
| `generation_prompt` / `edit_prompt` | 全局附加提示词 |
| `enable_generation` / `enable_edit` / `enable_prompt_polish` | 功能开关 |
| `available_aspect_ratios` | 全局可用宽高比 / 尺寸 |
| `aspect_ratio_field` | 宽高比写入字段（默认 `size`） |
| `response_image_path` | 响应图像路径（默认 `data`），支持 `data.url`、`data.*.url` 等写法 |
| `extra_request_body` | 全局额外请求体字段 |
| `timeout` | 全局请求超时（秒，默认 300） |
| `return_elapsed` / `return_id` / `return_model` / `return_retries` | 工具返回信息开关 |
| `model_order` | 模型优先顺序，可写 `来源名称/模型ID` 或仅模型 ID |

### 模型选择

工具的 `model` 参数枚举「来源名称/模型ID」标签，留空时按配置顺序执行；仅传入模型 ID 时匹配所有同名模型。

图像编辑请求以 JSON 提交：参考图放在 `images` 数组，每项形如 `{"image_url": "data:image/png;base64,..."}`，`mask` 使用相同结构。URL 或本地文件形式的参考图会先由插件下载、校验并转为 Base64 Data URI，以兼容不接受远端 URL 的 OpenAI 兼容路由。

## 聊天命令

除 LLM 工具外，插件还提供可直接使用的聊天命令（默认 `/t2i` 图像生成、`/i2i` 图像编辑）。命令由插件自行解析，不经过 AstrBot 的命令过滤器与 LLM 管线，因此不受服务端 `wake_prefix` 影响。

```
/t2i 一只坐在窗台上的橘猫，午后阳光
/i2i 换成赛博朋克风格 --size:1024x1024
```

| 规则 | 说明 |
| --- | --- |
| 命令头 | `command_generation_head` / `command_edit_head`，可配置多个（每行一项），大小写不敏感，必须与正文以空白分隔 |
| 命令触发前缀 | `command_prefix`（默认 `/`）；服务端已剥离前缀时，命令头仍可识别 |
| 提示词 | 命令头之后的全部内容，支持多行与空格 |
| 额外参数 | `--字段:值` 形式，作为请求体追加字段直接传给图像接口，例如 `--size:1024x1024`；行为由 `command_arg_mode` 控制 |
| 参数边界 | 自第一个 `--字段:` 起，其后的任何内容都不再视为提示词（提示词中单独出现的 `--` 不触发边界）；`listed` 模式下未列出的字段会被丢弃 |
| 图像编辑 | `/i2i` 需在同一条消息中附带图片，或引用一条含图片的消息；同一条消息可附带多张图片，会一起作为参考图提交 |

命令配置项：

| 配置项 | 说明 |
| --- | --- |
| `enable_commands` | 是否启用聊天命令 |
| `command_prefix` | 命令触发前缀（默认 `/`） |
| `command_generation_head` / `command_edit_head` | 命令头列表（默认 `["t2i"]` / `["i2i"]`），可配置多个 |
| `command_enable_polish` | 是否先由聊天模型润色命令提示词（默认关闭） |
| `command_polish_provider` | 润色使用的聊天模型提供商 ID，留空时使用当前会话模型 |
| `command_arg_mode` | 追加参数模式：`off` 禁止追加、`all` 允许任意字段、`listed` 仅允许已配置字段（默认） |
| `command_allowed_args` | `listed` 模式下允许的字段名列表（默认 `["size"]`），每行一项 |

## 区域管理

群聊 / 用户黑白名单与每人每日调用上限对**聊天命令和 LLM 工具调用同时生效**（润色工具仅做权限校验，不计数）。

| 配置项 | 说明 |
| --- | --- |
| `access_group_mode` | 群聊名单模式：`off` 不限制、`whitelist` 仅名单内群可用、`blacklist` 名单内群不可用 |
| `access_group_ids` | 群号列表，与 `access_group_mode` 配合使用 |
| `access_user_mode` | 用户名单模式，含义同上，对私聊与群聊中的发送者均生效 |
| `access_user_ids` | 用户 ID 列表 |
| `quota_daily_limit` | 每人每日调用上限，`0` 表示不限制（按 `平台:用户ID` 计数，本地日期切换时自动清零） |
| `checkin_enabled` | 是否允许通过签到补充当日额度 |
| `checkin_heads` | 签到命令头，默认 `["checkin"]`，与图像生成命令共用触发前缀 |
| `checkin_bonus` | 每次签到补充的次数 |
| `checkin_success` / `checkin_fail` | 签到成功 / 重复签到的回复模板，支持 `{{count}}`（本次获得）、`{{remaining}}`（今日剩余）、`{{limit}}`（每日上限） |

调用计数保存在 `data/plugin_data/astrbot_plugin_openai_image/usage.json`，跨日自动重置。

调用次数在发起请求前扣减；若本次调用未能产出图像（接口报错、返回文本、参考图缺失、蒙版无效等），该次数会自动返还，只有真正产出图像时才计入消耗。

## 可视化配置

在管理面板的插件详情中点击「打开视图」进入 `views/config/` 页面，支持：

- 服务来源的增删改、模型排序与多密钥管理（密钥默认掩码显示，可切换明文）
- 从接口获取模型列表并批量添加
- 全局模型调用顺序调整
- 各来源高级配置与全局参数的表单化编辑
- 聊天命令开关、多个命令头、命令触发前缀、追加参数模式与润色模型选择
- 区域管理：群聊 / 用户黑白名单、每日调用上限、签到命令头与自定义回复
- 右侧导航快速跳转，并跟随面板语言与主题

所有配置通过 Web API（`/astrbot_plugin_openai_image/config`）读写，效果与手动编辑配置文件一致。

## 代码结构

```
main.py            # 插件入口：注册、工具绑定、聊天命令、区域管理、Web API
src/
  commands.py      # 聊天命令解析与结果拆分
  access.py        # 黑白名单、每日额度与签到
  constants.py     # 工具名、润色提示词、响应字段常量
  config_access.py # 配置读取、模型计划与请求构造
  api_client.py    # 生成 / 编辑 / 润色请求
  reference_images.py # 参考图安全下载与校验
  tools.py         # LLM 工具定义
  response_utils.py# 响应解析与图像提取
  web_config.py    # 模板键补写与配置记录
views/
  config/          # 可视化配置视图
```

常见响应路径：

- `data` — 兼容 `data[].url` 与 `data[].b64_json`
- `data.0.url` — 仅取第一张图像的 URL
- `data.url` — `data` 为对象时使用

## 参考图下载

插件读取消息图片、引用图片与图片链接时，统一走内置的安全下载器，并受以下限制：

- 仅允许公网 HTTP(S) 地址，禁止内网、回环、链路本地与云元数据地址，重定向后会重新校验
- 仅允许 80、443、8080、8443 端口（接口返回的图片 URL 不受端口限制，但仍禁止内网地址）
- 单张图片不超过 20 MiB，且必须是 PNG / JPEG / WEBP / GIF / BMP
- 只接受未压缩传输（`Content-Encoding: identity`），不支持 gzip / br / deflate 响应的图片
- 单个文件 15 秒超时，整条消息的多张图片共用 20 秒总预算
- 不走系统代理（环境变量中的 `HTTP_PROXY` 等对取图无效），且仅使用 IPv4 解析，纯 IPv6 图床无法取图

消息中直接附带的图片会先解析为 Base64，因此不受上述网络限制；本地文件只允许读取 AstrBot 数据目录内的缓存图片。

## 错误提示

聊天中只会出现通用提示（如「图像生成失败，请稍后重试或联系管理员查看日志。」）。接口响应内容、来源与模型标识、密钥、图片链接与异常堆栈等细节一律仅写入 AstrBot 日志，便于排查而不泄露给用户。

## 社区贡献者

感谢所有为本项目提交代码、反馈问题与提出建议的人。

### 代码贡献

- [![qq875871130](https://avatars.githubusercontent.com/u/68939227?s=30) @qq875871130](https://github.com/qq875871130)
  - 引用图片编辑支持与参考图下载安全加固（[#1](https://github.com/XKPU/astrbot_plugin_openai_image/pull/1)）

欢迎通过 Pull 或 Issue 参与改进。

## 许可证

本项目基于 **GNU Affero General Public License v3.0 (AGPL-3.0)** 发布。

```
astrbot_plugin_openai_image - 可自定义的 OpenAI 兼容图像生成与图像编辑插件
Copyright (C) 2025 K_PU

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
