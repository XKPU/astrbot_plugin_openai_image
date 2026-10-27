"""LLM tool definitions for the OpenAI image plugin."""

from __future__ import annotations

from mcp import types as mcp_types

from astrbot.api import FunctionTool

from .constants import EDIT_TOOL_NAME, GENERATE_TOOL_NAME, POLISH_TOOL_NAME


class OpenAIImageFunctionTool(FunctionTool):
    """FunctionTool subclass kept in this package for correct plugin ownership."""


def _ratio_property(ratios: list[str] | None) -> dict:
    """Ratio schema; None means validation is off and any size is passed."""
    if not ratios:
        return {
            "type": "string",
            "description": (
                "Optional image size or aspect ratio (e.g. 1024x1024 or "
                "1:1), passed to the API without validation."
            ),
        }
    return {
        "type": "string",
        "description": ("Optional aspect ratio. Must be one of the configured values."),
        "enum": ratios,
    }


def _model_property(tags: list[str]) -> dict:
    return {
        "type": "string",
        "description": (
            'Optional model selector in "source_name/model_id" form. Leave '
            "empty to use the configured source and model order."
        ),
        "enum": tags,
    }


def build_tools(
    *,
    enable_generation: bool,
    enable_edit: bool,
    enable_prompt_polish: bool,
    generation_ratios: list[str] | None,
    edit_ratios: list[str] | None,
    generation_tags: list[str],
    edit_tags: list[str],
) -> list[FunctionTool]:
    """Build the LLM function tools according to the enabled features.

    generation_ratios / edit_ratios being None (instead of an empty list)
    means at least one participating source disabled ratio validation, so
    the aspect_ratio property becomes a free string without enum values.
    """
    tools: list[FunctionTool] = []

    if enable_generation:
        properties: dict = {
            "prompt": {
                "type": "string",
                "description": ("A detailed description of the image to generate."),
            },
        }
        if generation_tags:
            properties["model"] = _model_property(generation_tags)
        properties["aspect_ratio"] = _ratio_property(generation_ratios)
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
                    "properties": properties,
                    "required": ["prompt"],
                },
            ),
        )
    if enable_edit:
        properties = {
            "prompt": {
                "type": "string",
                "description": ("Instructions describing how to edit the image."),
            },
            "image": {
                "type": "string",
                "description": (
                    "Optional image URL, data URI, or base64 string. Leave "
                    "empty to use the first image attached to the user's message."
                ),
            },
            "mask": {
                "type": "string",
                "description": ("Optional mask image URL, data URI, or base64 string."),
            },
        }
        if edit_tags:
            properties["model"] = _model_property(edit_tags)
        properties["aspect_ratio"] = _ratio_property(edit_ratios)
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
                    "properties": properties,
                    "required": ["prompt"],
                },
            ),
        )
    if enable_prompt_polish:
        tools.append(
            OpenAIImageFunctionTool(
                name=POLISH_TOOL_NAME,
                description=(
                    "Rewrite a rough image idea into a detailed, "
                    "production-ready text-to-image prompt. Use this before "
                    "image generation when the user's prompt is short or vague."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The rough image prompt to polish.",
                        },
                    },
                    "required": ["prompt"],
                },
            ),
        )
    return tools


def tool_names() -> tuple[str, str, str]:
    """Return all tool names managed by this plugin."""
    return GENERATE_TOOL_NAME, EDIT_TOOL_NAME, POLISH_TOOL_NAME


def image_content(data: str, mime: str) -> mcp_types.ImageContent:
    """Build an image content block from base64 data."""
    return mcp_types.ImageContent(type="image", data=data, mimeType=mime)


def text_content(text: str) -> mcp_types.TextContent:
    """Build a text content block."""
    return mcp_types.TextContent(type="text", text=text)
