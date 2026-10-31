"""OpenAI-compatible image generation and editing plugin (entry point)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from mcp import types as mcp_types

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image, Plain, Reply
from astrbot.api.star import Context, Star, register
from astrbot.api.web import request as web_request
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_data_path

from .src import access as access_utils
from .src import api_client, web_config
from .src import commands as command_utils
from .src import tools as tool_defs
from .src.config_access import free_ratio, model_tags, ratio_options
from .src.constants import EDIT_TOOL_NAME, GENERATE_TOOL_NAME, POLISH_TOOL_NAME
from .src.reference_images import (
    ATTACHMENT_TIMEOUT,
    ReferenceImageError,
    attachment_image_urls,
    read_component_image,
    read_image,
)
from .src.response_utils import error_result, failure, has_image, result_text


@register(
    "openai_image",
    "K_PU",
    "可自定义的 OpenAI 兼容图像生成与图像编辑插件",
    "1.1.1",
)
class OpenAIImagePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}
        data_dir = Path(get_astrbot_plugin_data_path()) / "astrbot_plugin_openai_image"
        self._quota = access_utils.QuotaStore(data_dir / "usage.json")

    def _caller_key(self, event: AstrMessageEvent) -> str:
        """Build the quota key of the message sender."""
        platform = event.get_platform_name() or "unknown"
        return f"{platform}:{event.get_sender_id()}"

    def _access_denial(self, event: AstrMessageEvent) -> str:
        """Return the denial message for the current chat, or an empty string."""
        settings = access_utils.access_settings(self.config)
        return access_utils.verdict(
            settings,
            event.get_group_id() or "",
            event.get_sender_id() or "",
        )

    def _quota_denial(self, event: AstrMessageEvent) -> str:
        """Return the quota message when no daily call is left, else empty."""
        settings = access_utils.access_settings(self.config)
        limit = settings["daily_limit"]
        if limit <= 0:
            return ""
        key = self._caller_key(event)
        used, effective = self._quota.usage(key, limit)
        if used < effective:
            return ""
        return access_utils.quota_message(used, effective)

    def _quota_gate(self, event: AstrMessageEvent) -> access_utils.QuotaGate:
        """Build the per-request quota gate of the message sender."""
        settings = access_utils.access_settings(self.config)
        return access_utils.QuotaGate(
            self._quota,
            self._caller_key(event),
            settings["daily_limit"],
        )

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
        self.context.register_web_api(
            "/astrbot_plugin_openai_image/providers",
            self._web_list_providers,
            ["GET"],
            "获取可用于润色的聊天模型",
        )

    async def _web_list_providers(self):
        """List chat providers that can polish command prompts."""
        options = []
        for provider in self.context.get_all_providers():
            try:
                meta = provider.meta()
            except Exception as exc:
                logger.warning("Failed to read provider metadata: %s", exc)
                continue
            label = f"{meta.id} ({meta.model})" if meta.model else meta.id
            options.append({"id": meta.id, "label": label})
        return {"status": "ok", "data": {"providers": options}}

    async def _web_list_models(self):
        body = await web_request.json(default=None)
        if not isinstance(body, dict):
            body = {}
        api_base = str(body.get("api_base") or "").strip().rstrip("/")
        if not api_base:
            return {"status": "error", "message": "缺少接口地址", "data": {}}
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

    async def _attached_images(self, event: AstrMessageEvent) -> list[str]:
        """Return the base64 payloads of every image in the message.

        The images may be attached directly or inside a quoted reply, which the
        platform adapter fills with the referenced message components.

        Args:
            event: The current message event.

        Returns:
            The base64 payloads in encounter order, possibly empty.
        """
        messages = event.get_messages() or []
        replies = [item for item in messages if isinstance(item, Reply)]
        errors: list[str] = []
        found: list[str] = []
        groups = [("当前消息图片", messages)]
        groups.extend(
            ("引用图片", getattr(reply, "chain", None) or []) for reply in replies
        )
        # One shared budget for the whole message: a message quoting many images
        # must not hold the handler for the sum of every per-image timeout.
        try:
            async with asyncio.timeout(ATTACHMENT_TIMEOUT):
                for label, components in groups:
                    for component in components:
                        if not isinstance(component, Image):
                            continue
                        try:
                            found.append(await read_component_image(component))
                            logger.debug("%s提取成功", label)
                        except ReferenceImageError as exc:
                            errors.append(f"{label}: {exc}")
                            logger.debug("%s提取失败：%s", label, exc)

                # Only inspect text contained in Reply; never scan user input.
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
                                # Unlike explicit image parameters, attachment
                                # text must contain a URL, never a local path or
                                # inline payload.
                                if not url.lower().startswith(("http://", "https://")):
                                    raise ReferenceImageError(
                                        "引用附件只支持 HTTP(S) 图片链接。"
                                    )
                                found.append(await read_image(url))
                                logger.debug("QQ 引用附件文字解析成功，图片已读取")
                            except ReferenceImageError as exc:
                                errors.append("引用附件中的图片无法读取")
                                logger.debug("QQ 引用附件图片读取失败：%s", exc)
        except TimeoutError:
            raise ReferenceImageError(
                "提取图片超时，请减少引用图片数量或改用更快可访问的图片。"
            ) from None
        if found:
            return found
        if errors:
            logger.error(
                "openai_image: 参考图提取失败：%s", "；".join(dict.fromkeys(errors))
            )
            raise ReferenceImageError(
                "未获得有效参考图；请直接附图、引用包含图片的消息，"
                "或改用 HTTP(S) 公网图片链接。"
            )
        if replies:
            raise ReferenceImageError(
                "引用消息没有有效图片；可能引用了纯文字消息，或 QQOfficial "
                "未提供图片组件、附件内容或可访问链接，仅凭消息 ID 无法获取原图。"
            )
        return []

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_image_command(self, event: AstrMessageEvent) -> None:
        """Run the chat commands while keeping every failure out of the chat.

        The framework prints the exception text to the chat when a handler
        raises, so an unexpected failure is caught, logged and answered with a
        generic message here instead.
        """
        try:
            await self._run_image_command(event)
        except Exception as exc:
            logger.error("openai_image: 命令处理失败: %r", exc)
            if event.is_at_or_wake_command:
                await event.send(
                    event.plain_result("请求失败，请稍后重试或联系管理员查看日志。"),
                )
                event.stop_event()

    async def _run_image_command(self, event: AstrMessageEvent) -> None:
        """Handle the t2i/i2i chat commands outside the LLM pipeline.

        The wake stage may already have stripped the server wake prefix, so the
        raw text is matched here instead of relying on CommandFilter.
        """
        settings = command_utils.command_settings(self.config)
        checkin_heads = access_utils.access_settings(self.config)["checkin_heads"]
        if command_utils.parse_checkin(
            event.message_str,
            dict(settings, checkin_heads=checkin_heads),
            bool(event.is_at_or_wake_command),
        ):
            await self._handle_checkin(event)
            event.stop_event()
            return
        if not settings["enabled"]:
            return
        parsed = command_utils.parse_command(
            event.message_str,
            settings,
            bool(event.is_at_or_wake_command),
        )
        if parsed is None:
            return
        denial = self._access_denial(event)
        if denial:
            await event.send(event.plain_result(denial))
            event.stop_event()
            return
        prompt = parsed["prompt"]
        if not prompt:
            await event.send(event.plain_result("请输入提示词。"))
            event.stop_event()
            return
        quota_reply = self._quota_denial(event)
        if quota_reply:
            await event.send(event.plain_result(quota_reply))
            event.stop_event()
            return
        gate = self._quota_gate(event)
        if settings["polish"]:
            polished = await self._polish_command_prompt(
                event,
                prompt,
                settings["polish_provider"],
            )
            if polished:
                prompt = polished
        try:
            if parsed["kind"] == "generation":
                result = await api_client.generate_image(
                    self.config,
                    prompt,
                    extra_args=parsed["args"],
                    gate=gate,
                )
            else:
                try:
                    source_images = await self._attached_images(event)
                except ReferenceImageError as exc:
                    await event.send(event.plain_result(str(exc)))
                    event.stop_event()
                    return
                if not source_images:
                    await event.send(event.plain_result("请附带一张要编辑的图片。"))
                    event.stop_event()
                    return
                result = await api_client.edit_image(
                    self.config,
                    prompt,
                    source_images,
                    extra_args=parsed["args"],
                    gate=gate,
                )
        except Exception as exc:
            gate.settle(False)
            logger.error("openai_image: 命令处理失败: %r", exc)
            await event.send(
                event.plain_result("请求失败，请稍后重试或联系管理员查看日志。"),
            )
            event.stop_event()
            return
        gate.settle(has_image(result))
        await self._send_command_result(event, result)
        event.stop_event()

    async def _polish_command_prompt(
        self,
        event: AstrMessageEvent,
        prompt: str,
        provider_id: str,
    ) -> str:
        """Polish a command prompt with the configured polish provider."""
        provider = None
        if provider_id:
            try:
                provider = self.context.get_provider_by_id(provider_id)
            except Exception as exc:
                logger.warning(
                    "Failed to resolve polish provider %s: %s",
                    provider_id,
                    exc,
                )
        if provider is None:
            try:
                provider = self.context.get_using_provider(event.unified_msg_origin)
            except Exception as exc:
                logger.warning("Failed to resolve the chat model provider: %s", exc)
        if provider is None:
            logger.warning("No provider available to polish the command prompt.")
            return ""
        result = await api_client.polish_prompt(provider, prompt)
        polished = result_text(result)
        if "Polished prompt:" in polished:
            return polished.split("Polished prompt:", 1)[1].strip()
        logger.warning("Prompt polishing failed: %s", polished)
        return ""

    async def _send_command_result(
        self,
        event: AstrMessageEvent,
        result: mcp_types.CallToolResult,
    ) -> None:
        """Send the command result images and any remaining notes."""
        note, images = command_utils.result_payload(result)
        if images:
            chain = [Image.fromBase64(data) for data in images]
            if note:
                chain.insert(0, Plain(note))
            await event.send(event.chain_result(chain))
            return
        await event.send(event.plain_result(note or "请求失败，未返回图片。"))

    async def _handle_checkin(self, event: AstrMessageEvent) -> None:
        """Handle the check-in command: grant extra daily calls once a day."""
        settings = access_utils.access_settings(self.config)
        if not settings["checkin_enabled"]:
            await event.send(event.plain_result(access_utils.CHECKIN_DISABLED_MESSAGE))
            return
        denial = self._access_denial(event)
        if denial:
            await event.send(event.plain_result(denial))
            return
        limit = settings["daily_limit"]
        checked_now, granted, remaining = self._quota.checkin(
            self._caller_key(event),
            settings["checkin_bonus"],
            limit,
        )
        template = (
            settings["checkin_success"] if checked_now else settings["checkin_fail"]
        )
        await event.send(
            event.plain_result(
                access_utils.render(template, granted, remaining, limit),
            ),
        )

    async def polish_prompt(
        self,
        event: AstrMessageEvent,
        prompt: str,
    ) -> mcp_types.CallToolResult:
        try:
            denial = self._access_denial(event) if event is not None else ""
            if denial:
                return error_result(denial)
            umo = event.unified_msg_origin if event else None
            provider = self.context.get_using_provider(umo)
            if provider is None:
                return failure("没有可用的聊天模型可用于润色提示词。")
            return await api_client.polish_prompt(provider, prompt)
        except Exception as exc:
            logger.error("openai_image: prompt polishing failed: %r", exc)
            return failure("提示词润色失败，请稍后重试。")

    async def generate_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        model: str = "",
        aspect_ratio: str = "",
    ) -> mcp_types.CallToolResult:
        gate = None
        try:
            if event is not None:
                denial = self._access_denial(event) or self._quota_denial(event)
                if denial:
                    return error_result(denial)
                gate = self._quota_gate(event)
            result = await api_client.generate_image(
                self.config,
                prompt,
                aspect_ratio,
                model_tag=model,
                gate=gate,
            )
        except Exception as exc:
            if gate is not None:
                gate.settle(False)
            logger.error("openai_image: generation aborted: %r", exc)
            return failure("图像生成失败，请稍后重试或联系管理员查看日志。")
        if gate is not None:
            gate.settle(has_image(result))
        return result

    async def edit_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        image: str = "",
        mask: str = "",
        model: str = "",
        aspect_ratio: str = "",
        images: list[str] | None = None,
    ) -> mcp_types.CallToolResult:
        gate = None
        errors: list[str] = []
        sources: list[str] = []
        try:
            if event is not None:
                denial = self._access_denial(event) or self._quota_denial(event)
                if denial:
                    return error_result(denial)
                gate = self._quota_gate(event)
            try:
                sources = await self._attached_images(event)
            except ReferenceImageError as exc:
                errors.append(str(exc))
            # Explicit parameters are only a fallback: an image already found in
            # the message or its quote wins, so the same picture is never sent
            # twice by accident.
            if not sources:
                for value in [image, *(images or [])]:
                    if not (value or "").strip():
                        continue
                    try:
                        sources.append(await read_image(value))
                    except ReferenceImageError as exc:
                        errors.append(str(exc))
                        logger.debug("显式参考图片读取失败：%s", exc)
            if not sources:
                detail = (
                    "；".join(errors)
                    if errors
                    else "请在当前消息附图、引用包含图片的消息，或提供 image/images 参数。"
                )
                return failure("未获得有效参考图，未调用图片编辑 API。", detail)
            if (mask or "").strip():
                try:
                    mask = await read_image(mask)
                except ReferenceImageError as exc:
                    logger.debug("编辑蒙版读取失败：%s", exc)
                    return failure("编辑蒙版无效，未调用图片编辑 API。", exc)
            result = await api_client.edit_image(
                self.config,
                prompt,
                sources,
                mask,
                aspect_ratio,
                model_tag=model,
                gate=gate,
            )
        except Exception as exc:
            if gate is not None:
                gate.settle(False)
            logger.error("openai_image: edit aborted: %r", exc)
            return failure("图像编辑失败，请稍后重试或联系管理员查看日志。")
        if gate is not None:
            gate.settle(has_image(result))
        return result
