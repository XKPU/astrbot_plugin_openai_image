import base64
import binascii
import json
from typing import Any

import aiohttp
from mcp import types as mcp_types

from astrbot.api import AstrBotConfig, FunctionTool, logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, register

GENERATE_TOOL_NAME = "openai_image_generate"
EDIT_TOOL_NAME = "openai_image_edit"

_IMAGE_URL_KEYS = (
    "b64_json",
    "base64",
    "image_base64",
    "url",
    "image_url",
    "image",
)
_IMAGE_CONTAINER_KEYS = ("data", "images", "result", "output")


class OpenAIImageFunctionTool(FunctionTool):
    """FunctionTool subclass kept in this module for correct plugin ownership."""


def _error_result(message: str) -> mcp_types.CallToolResult:
    return mcp_types.CallToolResult(
        content=[mcp_types.TextContent(type="text", text=message)],
    )


def _walk_response(node: Any, parts: list[str]) -> list[Any]:
    """Resolve a dotted response path, fanning out across list values."""
    if not parts:
        return [node]
    part = parts[0]
    if isinstance(node, list):
        if part.isdigit():
            index = int(part)
            if 0 <= index < len(node):
                return _walk_response(node[index], parts[1:])
            return []
        if part in ("*", ""):
            results: list[Any] = []
            for item in node:
                results.extend(_walk_response(item, parts[1:]))
            return results
        results = []
        for item in node:
            results.extend(_walk_response(item, parts))
        return results
    if isinstance(node, dict):
        if part in node:
            return _walk_response(node[part], parts[1:])
        return []
    return []


def _collect_image_values(node: Any, output: list[str]) -> None:
    if isinstance(node, str):
        output.append(node)
    elif isinstance(node, list):
        for item in node:
            _collect_image_values(item, output)
    elif isinstance(node, dict):
        for key in _IMAGE_URL_KEYS:
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                output.append(value)
                return
        for key in _IMAGE_CONTAINER_KEYS:
            if key in node:
                _collect_image_values(node[key], output)
                return


def _extract_images(payload: Any, path: str) -> list[str]:
    """Extract image URL/base64 strings from the configured response path."""
    normalized = path.strip().replace("[", ".").replace("]", "") if path else ""
    parts = [part for part in normalized.split(".") if part]
    values: list[str] = []
    for node in _walk_response(payload, parts):
        _collect_image_values(node, values)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            deduplicated.append(value)
    return deduplicated


def _guess_mime(base64_data: str) -> str:
    head = base64_data[:32]
    if head.startswith("iVBOR"):
        return "image/png"
    if head.startswith("/9j/"):
        return "image/jpeg"
    if head.startswith("R0lGOD"):
        return "image/gif"
    if head.startswith("UklGR"):
        return "image/webp"
    if head.startswith("Qk"):
        return "image/bmp"
    try:
        raw = base64.b64decode(base64_data[:64] + "===", validate=False)
    except (binascii.Error, ValueError):
        return "image/png"
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"GIF8"):
        return "image/gif"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "image/webp"
    if raw.startswith(b"BM"):
        return "image/bmp"
    return "image/png"


def _split_image_value(value: str) -> tuple[str, str, str | None]:
    """Return (kind, data, mime) where kind is "url" or "base64"."""
    stripped = value.strip()
    if stripped.startswith(("http://", "https://")):
        return "url", stripped, None
    if stripped.startswith("data:"):
        header, _, data = stripped.partition(",")
        mime = header[5:].split(";", 1)[0] or None
        return "base64", "".join(data.split()), mime
    if stripped.startswith("base64://"):
        stripped = stripped[9:]
    data = "".join(stripped.split())
    return "base64", data, _guess_mime(data)


def _to_form_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _extension_for_mime(mime: str) -> str:
    return {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/bmp": "bmp",
    }.get(mime, "png")


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
        manager = self.context.get_llm_tool_manager()
        manager.remove_func(GENERATE_TOOL_NAME)
        manager.remove_func(EDIT_TOOL_NAME)

        tools: list[FunctionTool] = []
        if self.config.get("enable_generation", True):
            tools.append(
                OpenAIImageFunctionTool(
                    name=GENERATE_TOOL_NAME,
                    description=(
                        "Generate one or more images from a text prompt using an "
                        "OpenAI-compatible image API. Use this when the user asks "
                        "you to draw, create, or generate an image."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": (
                                    "A detailed description of the image to generate."
                                ),
                            },
                        },
                        "required": ["prompt"],
                    },
                    handler=self.generate_image,
                ),
            )
        if self.config.get("enable_edit", True):
            tools.append(
                OpenAIImageFunctionTool(
                    name=EDIT_TOOL_NAME,
                    description=(
                        "Edit or transform an existing image using a text prompt "
                        "with an OpenAI-compatible image API. If the user attached "
                        "an image and did not provide an image URL, leave the image "
                        "parameter empty to use the attached image."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": (
                                    "Instructions describing how to edit the image."
                                ),
                            },
                            "image": {
                                "type": "string",
                                "description": (
                                    "Optional image URL, data URI, or base64 string. "
                                    "Leave empty to use the first image attached to "
                                    "the user's message."
                                ),
                            },
                            "mask": {
                                "type": "string",
                                "description": (
                                    "Optional mask image URL, data URI, or base64 "
                                    "string."
                                ),
                            },
                        },
                        "required": ["prompt"],
                    },
                    handler=self.edit_image,
                ),
            )

        if tools:
            self.context.add_llm_tools(*tools)
            logger.info(
                "Registered OpenAI image tools: %s",
                ", ".join(tool.name for tool in tools),
            )
        else:
            logger.warning("Both OpenAI image generation and editing are disabled.")

    async def terminate(self) -> None:
        manager = self.context.get_llm_tool_manager()
        manager.remove_func(GENERATE_TOOL_NAME)
        manager.remove_func(EDIT_TOOL_NAME)

    def _api_settings(self) -> tuple[str, dict[str, str]]:
        base = (
            str(self.config.get("api_base") or "https://api.openai.com/v1")
            .strip()
            .rstrip("/")
        )
        headers: dict[str, str] = {}
        api_key = str(self.config.get("api_key") or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return base, headers

    def _timeout(self) -> aiohttp.ClientTimeout:
        try:
            seconds = float(self.config.get("timeout", 300))
        except (TypeError, ValueError):
            seconds = 300
        return aiohttp.ClientTimeout(total=max(seconds, 1))

    def _payload(self, prompt: str) -> dict[str, Any]:
        extra = self.config.get("extra_request_body") or {}
        payload = dict(extra) if isinstance(extra, dict) else {}
        payload["model"] = str(self.config.get("model") or "gpt-image-1").strip()
        payload["prompt"] = prompt
        return payload

    async def _fetch_bytes(
        self,
        session: aiohttp.ClientSession,
        url: str,
    ) -> tuple[bytes, str]:
        async with session.get(url) as response:
            response.raise_for_status()
            body = await response.read()
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if not mime or not mime.startswith("image/"):
            mime = _guess_mime(base64.b64encode(body).decode())
        return body, mime

    async def _load_image_bytes(
        self,
        session: aiohttp.ClientSession,
        value: str,
    ) -> tuple[bytes, str]:
        kind, data, mime = _split_image_value(value)
        if kind == "url":
            return await self._fetch_bytes(session, data)
        try:
            body = base64.b64decode(data, validate=False)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("The provided image is not valid Base64 data.") from exc
        return body, mime or _guess_mime(data)

    async def _attached_image(self, event: AstrMessageEvent) -> str:
        for component in event.get_messages():
            if isinstance(component, Image):
                try:
                    return await component.convert_to_base64()
                except Exception as exc:
                    logger.warning("Failed to read the attached image: %s", exc)
        return ""

    async def _handle_response(
        self,
        session: aiohttp.ClientSession,
        response: aiohttp.ClientResponse,
    ) -> mcp_types.CallToolResult:
        text = await response.text()
        if response.status < 200 or response.status >= 300:
            return _error_result(
                f"Image API request failed with HTTP {response.status}: {text[:2000]}",
            )
        try:
            payload: Any = json.loads(text) if text else {}
        except json.JSONDecodeError:
            return _error_result(
                f"Image API returned non-JSON content: {text[:2000]}",
            )

        path = str(self.config.get("response_image_path") or "data")
        image_values = _extract_images(payload, path)
        if not image_values:
            return _error_result(
                f"No image found in response field '{path}'. "
                f"Response preview: {text[:2000]}",
            )

        content: list[mcp_types.ContentBlock] = []
        notes: list[str] = [f"Returned {len(image_values)} image(s)."]
        for index, value in enumerate(image_values, start=1):
            kind, data, mime = _split_image_value(value)
            if kind == "url":
                notes.append(f"Image {index} URL: {data}")
                try:
                    body, mime = await self._fetch_bytes(session, data)
                except Exception as exc:
                    notes.append(
                        f"Image {index} could not be downloaded: {exc}. "
                        "Send it to the user using the URL above."
                    )
                    continue
                data = base64.b64encode(body).decode()
            content.append(
                mcp_types.ImageContent(
                    type="image",
                    data=data,
                    mimeType=mime or _guess_mime(data),
                ),
            )
            notes.append(f"Image {index} is attached.")

        content.insert(0, mcp_types.TextContent(type="text", text="\n".join(notes)))
        return mcp_types.CallToolResult(content=content)

    async def generate_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
    ) -> mcp_types.CallToolResult:
        base, headers = self._api_settings()
        headers["Content-Type"] = "application/json"
        payload = self._payload(prompt)
        try:
            async with aiohttp.ClientSession(timeout=self._timeout()) as session:
                async with session.post(
                    f"{base}/images/generations",
                    headers=headers,
                    json=payload,
                ) as response:
                    return await self._handle_response(session, response)
        except Exception as exc:
            logger.exception("Image generation request failed")
            return _error_result(f"Image generation request failed: {exc}")

    async def edit_image(
        self,
        event: AstrMessageEvent,
        prompt: str,
        image: str = "",
        mask: str = "",
    ) -> mcp_types.CallToolResult:
        source = (image or "").strip() or await self._attached_image(event)
        if not source:
            return _error_result(
                "No image was provided. Attach an image to the message or pass "
                "the image parameter.",
            )

        base, headers = self._api_settings()
        model = str(self.config.get("model") or "gpt-image-1").strip()
        extra = self.config.get("extra_request_body") or {}
        if not isinstance(extra, dict):
            extra = {}

        try:
            async with aiohttp.ClientSession(timeout=self._timeout()) as session:
                image_bytes, image_mime = await self._load_image_bytes(session, source)
                form = aiohttp.FormData()
                form.add_field("model", model)
                form.add_field("prompt", prompt)
                form.add_field(
                    "image",
                    image_bytes,
                    filename=f"image.{_extension_for_mime(image_mime)}",
                    content_type=image_mime,
                )
                if mask.strip():
                    mask_bytes, mask_mime = await self._load_image_bytes(
                        session,
                        mask,
                    )
                    form.add_field(
                        "mask",
                        mask_bytes,
                        filename=f"mask.{_extension_for_mime(mask_mime)}",
                        content_type=mask_mime,
                    )
                reserved = {"model", "prompt", "image", "mask"}
                for key, value in extra.items():
                    if str(key) in reserved:
                        continue
                    form.add_field(str(key), _to_form_value(value))

                async with session.post(
                    f"{base}/images/edits",
                    headers=headers,
                    data=form,
                ) as response:
                    return await self._handle_response(session, response)
        except Exception as exc:
            logger.exception("Image edit request failed")
            return _error_result(f"Image edit request failed: {exc}")
