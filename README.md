# OpenAI 图像生成与编辑

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/XKPU/astrbot_plugin_openai_image)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-AstrBot-purple)](https://github.com/Soulter/AstrBot)
[![Author](https://img.shields.io/badge/author-K__PU-orange)](https://github.com/XKPU)

为 AstrBot 提供 OpenAI 兼容的图像生成与编辑能力。支持任意实现 `/v1/images/generations` 和 `/v1/images/edits` 的 API 服务。

## 工具

插件为 LLM 注册三个工具：

| 工具 | 功能 |
| --- | --- |
| `openai_image_generate` | 根据文本提示词生成图像 |
| `openai_image_edit` | 编辑附带或传入的图像 |
| `openai_image_polish_prompt` | 将简短描述润色为详细的图像提示词（可关闭） |

## 配置

### 服务源

通过 `sources` 列表配置多个 API 来源，支持多 Key 轮询与多模型回退。

| 字段 | 说明 |
| --- | --- |
| `name` | 来源名称，生成模型标签 `名称/模型ID` |
| `api_base` | API 端点（如 `https://api.openai.com/v1`） |
| `models` | 模型列表，格式：`"模型ID"`、`"模型ID:重试次数"` 或 `{"id": ..., "retries": ...}` |
| `api_keys` | API Key 列表，轮询使用 |
| `enable_generation` / `enable_edit` | 是否参与生成 / 编辑 |
| `aspect_ratios` | 可用比例/尺寸，留空使用全局设置 |
| `aspect_ratio_field` | 比例字段名，留空使用全局（默认 `size`） |
| `validate_aspect_ratio` | 是否校验比例，关闭后任意尺寸原样透传 |
| `response_image_path` | 响应图片字段路径，留空使用全局（默认 `data`） |
| `generation_prompt` / `edit_prompt` | 提示词后缀，留空使用全局 |
| `extra_request_body` | 额外请求体参数，与全局合并（来源优先） |
| `timeout` | 请求超时秒数，`0` 使用全局 `timeout` |
| `enabled` | 是否启用该来源 |

请求顺序：来源列表 → 模型列表 → 每个 Key 重试 `次数+1` 次，失败后切换下一项。

### 全局配置

| 配置项 | 说明 |
| --- | --- |
| `generation_prompt` / `edit_prompt` | 全局提示词后缀 |
| `enable_generation` / `enable_edit` / `enable_prompt_polish` | 功能开关 |
| `available_aspect_ratios` | 全局比例/尺寸选项 |
| `aspect_ratio_field` | 比例字段名（默认 `size`） |
| `response_image_path` | 图像字段路径（默认 `data`），支持 `data.url`、`data.*.url` 等 |
| `extra_request_body` | 全局额外请求体 |
| `timeout` | 请求超时秒数（默认 300） |
| `return_elapsed` / `return_id` / `return_model` / `return_retries` | 工具返回信息开关 |
| `model_order` | 模型优先顺序列表，支持 `来源/模型ID` 或仅 `模型ID` |

### 模型选择

工具的 `model` 参数枚举 `来源名称/模型ID` 标签，留空按配置顺序执行。传入单个模型 ID 时匹配所有同名模型。

## 可视化配置

管理面板插件详情中点击「打开视图」进入 `views/config/` 页面，支持：

- 服务源增删改、模型排序、多 Key 管理（密码框掩码）
- 从 API 拉取模型并批量添加
- 全局模型使用顺序拖拽排序
- 每来源高级设置与全局表单化编辑
- 右侧导航快速跳转，跟随面板语言与主题

配置通过 Web API 读写（`/astrbot_plugin_openai_image/config`），与手动编辑配置文件等效。

## 代码结构

```
main.py            # 插件入口：注册、工具绑定、Web API
src/
  constants.py     # 工具名、润色 prompt、响应字段常量
  config_access.py # 配置读取、模型计划与请求构造
  api_client.py    # 生成/编辑/润色 HTTP 请求
  tools.py         # LLM 工具定义
  response_utils.py# 响应解析与图像提取
  web_config.py    # 模板键补写与工具函数
views/
  config/          # 可视化配置视图
```

常见响应路径：

- `data` — 兼容 `data[].url` 或 `data[].b64_json`
- `data.0.url` — 只取第一张图的 URL
- `data.url` — `data` 为对象时使用

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