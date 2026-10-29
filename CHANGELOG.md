# Changelog

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

[v1.0.1]: https://github.com/XKPU/astrbot_plugin_openai_image/compare/v1.0.0...v1.0.1
[v1.0.0]: https://github.com/XKPU/astrbot_plugin_openai_image/compare/aee1c1b7adc0af0cc483d50d9dff023af13ddb0c...v1.0.0