# Changelog

## [v1.1.0] - 2026-10-31

### 新增

- **聊天命令**：新增 `t2i`（图像生成）与 `i2i`（图像编辑）命令，直接在聊天中调用，不经过 LLM 管线
- **可配置命令头与命令触发前缀**：命令头支持多个（每行一个），大小写不敏感；命令触发前缀独立于服务端 `wake_prefix`
- **追加参数**：`--键:值` 形式的参数直接作为请求体字段传给图像接口，其后的内容不再视作提示词；提供禁止追加 / 允许任意 / 仅允许列出的参数名三档模式
- **命令润色**：可为命令单独指定润色模型，默认关闭
- **区域管理**：群聊与用户的黑白名单，对命令和 LLM 工具调用同时生效
- **每人每日调用上限**：按发送者计数，跨日自动清零，`0` 表示不限制
- **签到**：可配置签到命令头、每次补充次数与成功/重复签到回复模板，模板支持 `{{count}}`、`{{remaining}}`、`{{limit}}`
- **引用图片编辑**：`i2i` 支持引用消息中的图片
- **Web API**：新增 `/astrbot_plugin_openai_image/providers` 获取可用于润色的聊天模型

### 变更

- 可视化配置新增「聊天命令」与「区域管理」分区，导航调整为 8 个分区
- `src/` 包新增 `commands.py`（命令解析）与 `access.py`（名单、配额与签到）

## [v1.0.1] - 2026-10-29

### 变更

- **UI 术语规范化**：优化可视化配置界面及配置描述的中英文表述
- **README 与 CHANGELOG**：同步上述术语变更
- **metadata.yaml**：更新插件描述

## [v1.0.0] - 2026-10-27

### 新增

- **图像生成工具** (`openai_image_generate`)：通过 OpenAI 兼容 API 根据文本提示词生成图像
- **图像编辑工具** (`openai_image_edit`)：编辑消息附带或参数传入的图像，支持 Mask 蒙版
- **提示词润色工具** (`openai_image_polish_prompt`)：使用当前对话模型将简短描述润色为详细提示词
- **多服务源支持**：通过 `sources` 列表配置多个 API 来源，每来源独立设置模型、Key、超时等
- **多 Key 轮询与重试**：每来源支持多个 API Key 轮询，每模型可配置重试次数
- **模型回退链**：按来源列表 → 模型列表 → Key 列表顺序依次尝试，失败自动切换
- **全局模型顺序** (`model_order`)：自定义模型标签的优先执行顺序
- **比例/尺寸控制**：每来源独立配置比例选项与校验开关，关闭后任意尺寸原样透传
- **工具返回信息开关**：可按需返回请求用时、请求 ID、来源/模型标签、重试次数
- **可视化配置仪表盘**：`views/config/` 页面支持来源增删改、模型拖拽排序、API 拉取模型、多 Key 管理
- **Web API**：通过 `/astrbot_plugin_openai_image/config` 读写配置，`/astrbot_plugin_openai_image/models` 拉取模型列表

### 变更

- 从 helloworld 模板完全重写为完整插件
- 单体 `main.py` 拆分为模块化 `src/` 包（7 个模块）
- `_conf_schema.json` 扩展为多源模板列表格式
- `metadata.yaml` 更新插件元信息

[v1.1.0]: https://github.com/XKPU/astrbot_plugin_openai_image/compare/v1.0.1...v1.1.0
[v1.0.1]: https://github.com/XKPU/astrbot_plugin_openai_image/compare/v1.0.0...v1.0.1
[v1.0.0]: https://github.com/XKPU/astrbot_plugin_openai_image/compare/aee1c1b7adc0af0cc483d50d9dff023af13ddb0c...v1.0.0