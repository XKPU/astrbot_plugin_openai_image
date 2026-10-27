"""OpenAI-compatible image generation and editing plugin (entry point)."""

from __future__ import annotations

from mcp import types as mcp_types

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register
from astrbot.api.web import request as web_request

from .src import api_client, web_config
from .src import tools as tool_defs
from .src.config_access import free_ratio, model_tags, ratio_options
from .src.constants import EDIT_TOOL_NAME, GENERATE_TOOL_NAME, POLISH_TOOL_NAME
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
            "拉取来源的可用模型列表",
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
        for component in event.get_messages():
            if isinstance(component, Image):
                try:
                    return await component.convert_to_base64()
                except Exception as exc:
                    logger.warning("Failed to read the attached image: %s", exc)
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
        source = (image or "").strip() or await self._attached_image(event)
        if not source:
            return error_result(
                "No image was provided. Attach an image to the message or pass "
                "the image parameter.",
            )
        return await api_client.edit_image(
            self.config,
            prompt,
            source,
            mask,
            aspect_ratio,
            model_tag=model,
        )
