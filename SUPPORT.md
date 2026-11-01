# 支持

插件的一般说明见 [README.md](README.md)。

## 目录

- [提问之前](#提问之前)
- [报告缺陷与建议](#报告缺陷与建议)
- [不在支持范围内](#不在支持范围内)
- [安全](#安全)
- [参与贡献](#参与贡献)
- [许可](#许可)

## 提问之前

下面覆盖最常见的问题。

### LLM 无法调用工具

1. **检查功能开关**：确认 `enable_generation`、`enable_edit` 已开启，且至少配置了一个启用的来源及其模型。
2. **检查来源启用状态**：至少一个来源的 `enabled` 必须为 `true`。

### 图像生成 / 编辑返回失败

排查步骤：

1. **检查 API 地址**：`api_base` 应包含 `/v1`（如 `https://api.openai.com/v1`），插件会自动拼接 `/images/generations` 或 `/images/edits`。
2. **检查 API Key**：确保 Key 有效且未过期。多 Key 配置时插件会按列表顺序轮询。
3. **检查模型 ID**：模型 ID 必须与 API 服务实际提供的名称一致。可通过可视化配置中的「从接口获取」按钮拉取模型列表。
4. **检查响应路径**：`response_image_path` 默认为 `data`。如果接口返回结构与 OpenAI 不同（如图片在 `output` 字段中），需相应调整。常见写法见 [README 代码结构](README.md#代码结构)。

### 图像编辑提示"参考图无效"

图像编辑 (`/i2i` 或 `openai_image_edit`) 需要附带参考图：

- **直接发送图片**：在消息中附带图片，或 `/i2i` 命令同一条消息中携带图片。
- **引用含图消息**：回复一条包含图片的消息再执行 `/i2i`。
- **参考图下载限制**：通过 URL 引用的图片仅允许公网 HTTP(S) 地址，端口限制为 80、443、8080、8443，单张不超过 20 MiB，格式仅限 PNG / JPEG / WEBP / GIF / BMP。消息中直接附带的图片无此限制。
- **编辑请求格式**：本插件以 JSON 提交图像编辑请求（非 multipart），参考图通过 `images` 数组以 Base64 Data URI 传输。如果你的 API 服务不支持此格式，图像编辑将失败。

### 聊天命令不生效

命令 `/t2i`、`/i2i` 由插件自行解析，不经过 AstrBot 命令过滤器：

1. **检查命令开关**：确认 `enable_commands` 为 `true`。
2. **命令头与正文之间必须有空白分隔**
3. **命令触发前缀**：`command_prefix` 默认为 `/`，可自定义。服务端已剥离前缀时（如 AstrBot 的 `wake_prefix`），命令头仍可识别。
4. **群聊 / 用户黑白名单**：确认当前群或用户未被限制（见 `access_group_mode` / `access_user_mode`）。
5. **追加参数**：`--字段:值` 之后的任何内容都不再视作提示词。

### 每日调用次数已用完

- 每日调用上限由 `quota_daily_limit` 控制，`0` 表示不限制。
- 计数按 `平台:用户ID` 区分，本地日期切换时自动清零。
- 调用次数在发起请求前扣减；若本次调用未产出图像（接口报错、参考图缺失等），次数会自动返还。

### 多来源轮询未按预期切换

请求顺序：按来源列表顺序 → 模型列表顺序依次尝试。每个 Key 按「重试次数 + 1」次请求后切换下一个 Key。

- **全局模型顺序**：`model_order` 可调整优先执行顺序。
- **重试次数**：在模型配置中通过 `模型ID:重试次数` 或 `{"id": "...", "retries": ...}` 设置。

### 宽高比 / 尺寸参数未生效

- 全局可用宽高比由 `available_aspect_ratios` 配置，每来源可通过 `aspect_ratios` 覆盖。
- `aspect_ratio_field` 控制写入请求体的字段名（默认 `size`）。
- `validate_aspect_ratio` 关闭后，任意尺寸将原样透传而不校验。

## 报告缺陷与建议

缺陷报告、功能建议与使用疑问，请提交到 GitHub Issues：

[https://github.com/XKPU/astrbot_plugin_openai_image/issues](https://github.com/XKPU/astrbot_plugin_openai_image/issues)

### 一份有用的缺陷报告通常包含

1. **你做了什么** —— 导致问题的操作步骤。
2. **预期结果** 与 **实际结果**。
3. **环境** —— AstrBot 版本、插件版本、Python 版本、操作系统。
4. **AstrBot 日志** —— 请裁剪出错的那一步，最好为 Debug 日志等级下，并隐去日志中的 API Key 等敏感信息。

> **请勿附带含有 API Key 或个人数据的日志或配置文件。**

## 不在支持范围内

- **非 OpenAI 兼容的 API。** 本插件仅支持 OpenAI 兼容的 `/v1/images/generations` 与 `/v1/images/edits` 端点。
- **图像编辑的 multipart 格式。** 插件以 JSON 请求体提交图像编辑，如果你的 API 要求 multipart 表单格式，则不受支持。
- **非公网图床。** 参考图下载仅允许公网 HTTP(S) 地址，内网、回环、链路本地地址均被禁止。

## 安全

发现安全问题请**不要**开公开 issue。可通过以下渠道私下报告：

- GitHub 安全公告：[https://github.com/XKPU/astrbot_plugin_openai_image/security/advisories/new](https://github.com/XKPU/astrbot_plugin_openai_image/security/advisories/new)
- 邮箱：`csaxongmail@gmail.com` 或 `u-eptm@u-eptm.top`

更详细的内容见 [SECURITY.md](SECURITY.md)。

## 参与贡献

欢迎提交 Pull Request 或参与 Issue 讨论。

提交前请确保：

- 代码通过 Ruff 格式化。
- 代码功能通过测试。

**未完成或未经测试的提交**同样欢迎，请在提交时说明其状态。

## 许可

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