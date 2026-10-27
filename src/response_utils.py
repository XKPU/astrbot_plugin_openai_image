"""Pure helpers for parsing OpenAI-compatible image API responses."""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any

from mcp import types as mcp_types

from .constants import IMAGE_CONTAINER_KEYS, IMAGE_URL_KEYS


def error_result(message: str) -> mcp_types.CallToolResult:
    """Build a tool result carrying a single text error message."""
    return mcp_types.CallToolResult(
        content=[mcp_types.TextContent(type="text", text=message)],
    )


def image_content(data: str, mime: str) -> mcp_types.ImageContent:
    """Build an image content block from base64 data and a MIME type."""
    return mcp_types.ImageContent(
        type="image",
        data=data,
        mimeType=mime,
    )


def text_content(text: str) -> mcp_types.TextContent:
    """Build a text content block."""
    return mcp_types.TextContent(type="text", text=text)


def has_image(result: mcp_types.CallToolResult) -> bool:
    """Check whether a tool result contains any image content block."""
    return any(getattr(item, "type", None) == "image" for item in result.content)


def result_text(result: mcp_types.CallToolResult) -> str:
    """Return the first text block of a tool result."""
    for item in result.content:
        if isinstance(item, mcp_types.TextContent):
            return item.text
    return "Unknown error."


def walk_response(node: Any, parts: list[str]) -> list[Any]:
    """Resolve a dotted response path, fanning out across list values."""
    if not parts:
        return [node]
    part = parts[0]
    if isinstance(node, list):
        if part.isdigit():
            index = int(part)
            if 0 <= index < len(node):
                return walk_response(node[index], parts[1:])
            return []
        if part in ("*", ""):
            results: list[Any] = []
            for item in node:
                results.extend(walk_response(item, parts[1:]))
            return results
        results = []
        for item in node:
            results.extend(walk_response(item, parts))
        return results
    if isinstance(node, dict):
        if part in node:
            return walk_response(node[part], parts[1:])
        return []
    return []


def collect_image_values(node: Any, output: list[str]) -> None:
    """Collect image URL/base64 strings from a response node by key priority."""
    if isinstance(node, str):
        output.append(node)
    elif isinstance(node, list):
        for item in node:
            collect_image_values(item, output)
    elif isinstance(node, dict):
        for key in IMAGE_URL_KEYS:
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                output.append(value)
                return
        for key in IMAGE_CONTAINER_KEYS:
            if key in node:
                collect_image_values(node[key], output)
                return


def extract_images(payload: Any, path: str) -> list[str]:
    """Extract image URL/base64 strings from the configured response path."""
    normalized = path.strip().replace("[", ".").replace("]", "") if path else ""
    parts = [part for part in normalized.split(".") if part]
    values: list[str] = []
    for node in walk_response(payload, parts):
        collect_image_values(node, values)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            deduplicated.append(value)
    return deduplicated


def guess_mime(base64_data: str) -> str:
    """Guess an image MIME type from base64 magic bytes."""
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


def split_image_value(value: str) -> tuple[str, str, str | None]:
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
    return "base64", data, guess_mime(data)


def to_form_value(value: Any) -> str:
    """Convert an extra-request-body value into a multipart form string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def extension_for_mime(mime: str) -> str:
    """Map an image MIME type to a file extension."""
    return {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/bmp": "bmp",
    }.get(mime, "png")
