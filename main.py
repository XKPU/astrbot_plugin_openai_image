"""OpenAI-compatible image generation and editing plugin (entry point)."""

from __future__ import annotations

from mcp import types as mcp_types

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image, Plain, Reply
from astrbot.api.star import Context, Star, register
from astrbot.api.web import request as web_request

from .src import api_client, web_config
from .src import tools as tool_defs
from .src.config_access import free_ratio, model_tags, ratio_options
from .src.constants import EDIT_TOOL_NAME, GENERATE_TOOL_NAME, POLISH_TOOL_NAME
from .src.reference_images import (
    ReferenceImageError,
    attachment_image_urls,
    read_component_image,
    read_image,
)
from .src.response_utils import error_result


@register(
    "openai_image",
    "K_PU",
    "可自定义的 OpenAI 兼容图像生成与图像编辑插件",
    "1.0.0",
)
class OpenAIImagePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}

    async def initialize(self) -> None:
        # Stamp the template key so the declarative settings page accepts
        # sources saved through the visual config view.
        if web_config.ensure_template_keys(self.config):
            self.config.save_config()
        manager = self.context.get_llm_tool_manager()
        for name in (GENERATE_TOOL_NAME, EDIT_TOOL_NAME, POLISH_TOOL_NAME):
            manager.remove_func(name)

        tools = tool_defs.build_tools(
            enable_generation=self.config.get("enable_generation", True)
            and bool(model_tags(self.config, "generation")),
            enable_edit=self.config.get("enable_edit", True)
            and bool(model_tags(self.config, "edit")),
            enable_prompt_polish=self.config.get("enable_prompt_polish", True),
            generation_ratios=None
            if free_ratio(self.config, "generation")
            else ratio_options(self.config, "generation"),
            edit_ratios=None
            if free_ratio(self.config, "edit")
            else ratio_options(self.config, "edit"),
            generation_tags=model_tags(self.config, "generation"),
            edit_tags=model_tags(self.config, "edit"),
        )
        for tool in tools:
            if tool.name == GENERATE_TOOL_NAME:
                tool.handler = self.generate_image
            elif tool.name == EDIT_TOOL_NAME:
                tool.handler = self.edit_image
            elif tool.name == POLISH_TOOL_NAME:
                tool.handler = self.polish_prompt

        if tools:
            self.context.add_llm_tools(*tools)
            logger.info(
                "Registered OpenAI image tools: %s",
                ", ".join(tool.name for tool in tools),
            )
        else:
            logger.warning("All OpenAI image plugin features are disabled.")
        # Register the config API even when every tool is off, so the
        # dashboard view can still read and restore the configuration.
        self._register_web_apis()

    async def terminate(self) -> None:
        manager = self.context.get_llm_tool_manager()
        for name in (GENERATE_TOOL_NAME, EDIT_TOOL_NAME, POLISH_TOOL_NAME):
            manager.remove_func(name)

    def _register_web_apis(self) -> None:
        """Expose config read/write endpoints for the dashboard config view."""
        self.context.register_web_api(
            "/astrbot_plugin_openai_image/config",
            self._web_get_config,
            ["GET"],
            "获取插件配置",
        )
        self.context.register_web_api(
            "/astrbot_plugin_openai_image/config",
            self._web_save_config,
            ["POST"],
            "保存插件配置",
        )
        self.context.register_web_api(
            "/astrbot_plugin_openai_image/models",
            self._web_list_models,
            ["POST"],
            "获取来源的可用模型列表",
        )

    async def _web_list_models(self):
        body = await web_request.json(default=None)
        if not isinstance(body, dict):
            body = {}
        api_base = str(body.get("api_base") or "").strip().rstrip("/")
        if not api_base:
            return {"status": "error", "message": "缺少 API 地址", "data": {}}
        keys = body.get("api_keys")
        if not isinstance(keys, list):
            keys = []
        resolved_keys = [str(key).strip() for key in keys if str(key).strip()]
        try:
            models = await api_client.fetch_models(api_base, resolved_keys)
        except Exception as exc:
            logger.warning("Model list request failed for %s: %s", api_base, exc)
            return {"status": "error", "message": str(exc), "data": {}}
        return {"status": "ok", "data": {"models": models}}

    async def _web_get_config(self):
        return {"status": "ok", "data": dict(self.config)}

    async def _web_save_config(self):
        body = await web_request.json(default=None)
        if not isinstance(body, dict) or not isinstance(body.get("config"), dict):
            return {"status": "error", "message": "无效的配置数据", "data": {}}
        self.config.update(body["config"])
        self.config.save_config()
        web_config.log_config_update(web_request.username)
        await self.initialize()
        return {"status": "ok", "data": dict(self.config)}

    async def _attached_image(self, event: AstrMessageEvent) -> str:
        messages = event.get_messages() or []
        replies = [item for item in messages if isinstance(item, Reply)]
        errors: list[str] = []
        groups = [("当前消息图片", messages)]
        groups.extend(
            ("引用图片", getattr(reply, "chain", None) or []) for reply in replies
        )
        for label, components in groups:
            for component in components:
                if not isinstance(component, Image):
                    continue
                try:
                    data = await read_component_image(component)
                    logger.debug("%s提取成功", label)
                    return data
                except ReferenceImageError as exc:
                    errors.append(str(exc))
                    logger.debug("%s提取失败：%s", label, exc)

        # Only inspect text contained in Reply; never scan the user's input.
        seen_urls: set[str] = set()
        for reply in replies:
            texts = [
                item.text
                for item in (getattr(reply, "chain", None) or [])
                if isinstance(item, Plain)
            ]
            texts.append(getattr(reply, "message_str", None) or "")
            for text in texts:
                for url in attachment_image_urls(text):
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    try:
                        # Unlike explicit image parameters, attachment text must
                        # contain a URL, never a local path or inline payload.
                        if not url.lower().startswith(("http://", "https://")):
                            raise ReferenceImageError("引用附件只支持 HTTP(S) 图片链接。")
                        data = await read_image(url)
                        logger.debug("QQ 引用附件文字解析成功，图片已读取")
                        return data
                    except ReferenceImageError as exc:
                        errors.append(str(exc))
                        logger.debug("QQ 引用附件图片读取失败：%s", exc)
        if replies:
            logger.debug("引用消息没有有效图片")
        if errors:
            raise ReferenceImageError("；".join(dict.fromkeys(errors)))
        if replies:
            raise ReferenceImageError(
                "引用消息没有有效图片；可能引用了纯文字消息，或 QQOfficial "
                "未提供图片组件、附件内容或可访问链接，仅凭消息 ID 无法获取原图。"
            )
        return ""

    async def polish_prompt(
        self,
        event: AstrMessageEvent,
        prompt: str,
    ) -> mcp_types.CallToolResult:
        umo = event.unified_msg_origin if event else None
        try:
            provider = self.context.get_using_provider(umo)
        except Exception as exc:
            return error_result(
                f"Failed to resolve the chat model provider: {exc}",
            )
        if provider is None:
            return error_result(
                "No chat model provider is available to polish the prompt.",
            )
        return await api_client.polish_prompt(provider, prompt)

    async def generate_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        model: str = "",
        aspect_ratio: str = "",
    ) -> mcp_types.CallToolResult:
        return await api_client.generate_image(
            self.config,
            prompt,
            aspect_ratio,
            model_tag=model,
        )

    async def edit_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        image: str = "",
        mask: str = "",
        model: str = "",
        aspect_ratio: str = "",
    ) -> mcp_types.CallToolResult:
        errors: list[str] = []
        try:
            source = await self._attached_image(event)
        except ReferenceImageError as exc:
            source = ""
            errors.append(str(exc))
        if not source and (image or "").strip():
            try:
                source = await read_image(image)
            except ReferenceImageError as exc:
                errors.append(str(exc))
                logger.debug("显式参考图片读取失败：%s", exc)
        if not source:
            detail = "；".join(errors) if errors else (
                "请在当前消息附图、引用包含图片的消息，或提供 image 参数。"
            )
            return error_result(
                "未获得有效参考图，未调用图片编辑 API。" + detail,
            )
        if (mask or "").strip():
            try:
                mask = await read_image(mask)
            except ReferenceImageError as exc:
                logger.debug("编辑蒙版读取失败：%s", exc)
                return error_result(f"编辑蒙版无效，未调用图片编辑 API：{exc}")
        return await api_client.edit_image(
            self.config,
            prompt,
            source,
            mask,
            aspect_ratio,
            model_tag=model,
        )
