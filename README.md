# OpenAI 图像生成与编辑插件

为 LLM 注册两个工具：

- `openai_image_generate`：根据文本提示词生成图像。
- `openai_image_edit`：编辑用户消息中附带的图像，或编辑通过参数传入的图像。

插件兼容 OpenAI 图像 API，也可用于提供 `/v1/images/generations` 和 `/v1/images/edits` 的服务。

## 配置

在 AstrBot 管理面板的插件配置中设置：

| 配置项 | 说明 |
| --- | --- |
| `api_base` | API 端点，填写到 `/v1`，例如 `https://api.openai.com/v1`。插件会自动拼接 `/images/generations` 与 `/images/edits`。 |
| `api_key` | API Key。留空时不发送 `Authorization` 请求头。 |
| `model` | 模型 ID，例如 `gpt-image-1`、`dall-e-3`。 |
| `enable_generation` | 是否注册图像生成工具。 |
| `enable_edit` | 是否注册图像编辑工具。 |
| `response_image_path` | 响应中图像字段的路径，默认 `data`。支持 `data.url`、`data.0.url`、`data.*.url` 等写法。 |
| `extra_request_body` | 合并到生成请求 JSON 中的额外参数；编辑请求中会作为额外的 multipart 字段。 |
| `timeout` | 请求超时时间，单位秒。 |

插件会自动识别响应中的 HTTP URL、Data URI 和 Base64 数据，并将图像返回给 LLM。

## 示例

`extra_request_body`：

```json
{
  "size": "1024x1024",
  "quality": "high"
}
```

常见响应路径：

- `data`：兼容返回 `data[].url` 或 `data[].b64_json` 的接口。
- `data.0.url`：只取第一张图的 URL。
- `data.url`：`data` 为对象时使用。
