"""HTTP request layer for OpenAI-compatible image APIs."""

from __future__ import annotations

import base64
import binascii
import json
import time
from typing import Any

import aiohttp
from mcp import types as mcp_types

from .config_access import (
    generation_payload,
    merged_extra,
    model_plan,
    prompt_for,
    ratio_field,
    request_timeout,
    return_info_flags,
)
from .constants import POLISH_SYSTEM_PROMPT
from .response_utils import (
    error_result,
    extension_for_mime,
    extract_images,
    guess_mime,
    has_image,
    image_content,
    result_text,
    split_image_value,
    text_content,
    to_form_value,
)


async def fetch_bytes(
    session: aiohttp.ClientSession,
    url: str,
) -> tuple[bytes, str]:
    """Download an image and return (bytes, mime)."""
    async with session.get(url) as response:
        response.raise_for_status()
        body = await response.read()
        mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
    if not mime or not mime.startswith("image/"):
        mime = guess_mime(base64.b64encode(body).decode())
    return body, mime


async def load_image_bytes(
    session: aiohttp.ClientSession,
    value: str,
) -> tuple[bytes, str]:
    """Load image bytes from a URL, data URI, or base64 string."""
    kind, data, mime = split_image_value(value)
    if kind == "url":
        return await fetch_bytes(session, data)
    try:
        body = base64.b64decode(data, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The provided image is not valid Base64 data.") from exc
    return body, mime or guess_mime(data)


def _info_header(
    tag: str,
    response_id: str,
    elapsed: float,
    retries_used: int,
    flags: dict[str, bool],
) -> str | None:
    """Build the return-info line shown to the LLM when enabled."""
    parts: list[str] = []
    if flags.get("model"):
        parts.append(f"model: {tag}")
    if flags.get("id") and response_id:
        parts.append(f"id: {response_id}")
    if flags.get("elapsed"):
        parts.append(f"elapsed: {elapsed:.2f}s")
    if flags.get("retries"):
        parts.append(f"retries: {retries_used}")
    return " | ".join(parts) if parts else None


async def fetch_models(
    api_base: str,
    api_keys: list[str] | None = None,
) -> list[str]:
    """Fetch the model list from an OpenAI-compatible /models endpoint.

    Tries each key in order and returns the deduplicated model ids from
    the first response that contains any.
    """
    endpoint = f"{api_base.rstrip('/')}/models"
    keys = [key for key in (api_keys or []) if key] or [""]
    errors: list[str] = []
    for api_key in keys:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            ) as session:
                async with session.get(endpoint, headers=headers) as response:
                    text = await response.text()
                    if response.status < 200 or response.status >= 300:
                        errors.append(f"HTTP {response.status}: {text[:200]}")
                        continue
                    payload = json.loads(text) if text else {}
        except Exception as exc:
            errors.append(str(exc))
            continue
        data = payload.get("data") if isinstance(payload, dict) else payload
        ids: list[str] = []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    model_id = str(
                        entry.get("id")
                        or entry.get("model")
                        or entry.get("name")
                        or "",
                    ).strip()
                else:
                    model_id = str(entry).strip()
                if model_id and model_id not in ids:
                    ids.append(model_id)
        if ids:
            return ids
        errors.append("No models found in the response.")
    raise RuntimeError("; ".join(errors) or "Model list request failed.")


async def handle_response(
    session: aiohttp.ClientSession,
    response: aiohttp.ClientResponse,
    response_image_path: str,
) -> tuple[mcp_types.CallToolResult, str]:
    """Turn an image API response into (tool result, response id)."""
    text = await response.text()
    if response.status < 200 or response.status >= 300:
        return error_result(
            f"Image API request failed with HTTP {response.status}: {text[:2000]}",
        ), ""
    try:
        payload: Any = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return error_result(
            f"Image API returned non-JSON content: {text[:2000]}",
        ), ""
    response_id = ""
    if isinstance(payload, dict):
        response_id = str(payload.get("id") or "")

    image_values = extract_images(payload, response_image_path)
    if not image_values:
        return error_result(
            f"No image found in response field '{response_image_path}'. "
            f"Response preview: {text[:2000]}",
        ), response_id

    content: list[mcp_types.ContentBlock] = []
    notes: list[str] = [f"Returned {len(image_values)} image(s)."]
    for index, value in enumerate(image_values, start=1):
        kind, data, mime = split_image_value(value)
        if kind == "url":
            notes.append(f"Image {index} URL: {data}")
            try:
                body, mime = await fetch_bytes(session, data)
            except Exception as exc:
                notes.append(
                    f"Image {index} could not be downloaded: {exc}. "
                    "Send it to the user using the URL above.",
                )
                continue
            data = base64.b64encode(body).decode()
        content.append(image_content(data, mime or guess_mime(data)))
        notes.append(f"Image {index} is attached.")

    content.insert(0, text_content("\n".join(notes)))
    return mcp_types.CallToolResult(content=content), response_id


async def _post_edit(
    session: aiohttp.ClientSession,
    source: dict[str, Any],
    config: Any,
    model_id: str,
    prompt: str,
    aspect_ratio: str,
    headers: dict[str, str],
    image_bytes: bytes | None,
    image_mime: str,
    mask_bytes: bytes | None,
    mask_mime: str,
    extra_args: dict[str, Any] | None = None,
) -> mcp_types.CallToolResult:
    """Send one multipart edit request and normalize the response."""
    extra = merged_extra(config, source)
    field = source["aspect_ratio_field"] or ratio_field(config)
    reserved = {"model", "prompt", "image", "mask"}
    if aspect_ratio:
        reserved.add(field)

    form = aiohttp.FormData()
    form.add_field("model", model_id)
    form.add_field("prompt", prompt)
    if aspect_ratio:
        form.add_field(field, aspect_ratio)
    form.add_field(
        "image",
        image_bytes,
        filename=f"image.{extension_for_mime(image_mime)}",
        content_type=image_mime,
    )
    if mask_bytes is not None and mask_mime:
        form.add_field(
            "mask",
            mask_bytes,
            filename=f"mask.{extension_for_mime(mask_mime)}",
            content_type=mask_mime,
        )
    for key, value in extra.items():
        if str(key) in reserved:
            continue
        form.add_field(str(key), to_form_value(value))
    for key, value in (extra_args or {}).items():
        if str(key) in reserved:
            continue
        form.add_field(str(key), to_form_value(value))

    # Per-source override wins over the global response_image_path.
    response_path = str(
        source.get("response_image_path") or config.get("response_image_path") or "data"
    )
    async with session.post(
        f"{source['api_base']}/images/edits",
        headers=headers,
        data=form,
    ) as response:
        return await handle_response(session, response, response_path)


async def _execute_plan_item(
    config: Any,
    plan_item: dict[str, Any],
    kind: str,
    prompt: str,
    aspect_ratio: str = "",
    image: str = "",
    mask: str = "",
    extra_args: dict[str, Any] | None = None,
) -> mcp_types.CallToolResult:
    """Run one plan item (source + model): keys x retries, then the request.

    kind is "generation" (JSON POST /images/generations) or "edit"
    (multipart POST /images/edits). Returns the first result carrying an
    image; failure notes are accumulated otherwise. extra_args are appended
    verbatim to the request body (command arguments).
    """
    source = plan_item["source"]
    tag = plan_item["tag"]
    attempts = plan_item["retries"] + 1
    flags = return_info_flags(config)
    # Per-source override wins over the global response_image_path.
    response_path = str(
        source.get("response_image_path") or config.get("response_image_path") or "data"
    )
    errors: list[str] = []
    retries_used = 0
    started = time.monotonic()

    try:
        async with aiohttp.ClientSession(
            timeout=request_timeout(config, source),
        ) as session:
            image_bytes = None
            mask_bytes = None
            image_mime = mask_mime = ""
            if kind == "edit":
                image_bytes, image_mime = await load_image_bytes(session, image)
                if mask.strip():
                    mask_bytes, mask_mime = await load_image_bytes(session, mask)

            for key_index, api_key in enumerate(source["api_keys"], start=1):
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                label = f"{tag} key {key_index}"
                for attempt in range(attempts):
                    if attempt:
                        retries_used += 1
                    try:
                        if kind == "generation":
                            payload = generation_payload(
                                config,
                                source,
                                plan_item["model"],
                                prompt,
                                aspect_ratio,
                                extra_args,
                            )
                            headers["Content-Type"] = "application/json"
                            async with session.post(
                                f"{source['api_base']}/images/generations",
                                headers=headers,
                                json=payload,
                            ) as response:
                                result, response_id = await handle_response(
                                    session,
                                    response,
                                    response_path,
                                )
                        else:
                            result, response_id = await _post_edit(
                                session,
                                source,
                                config,
                                plan_item["model"],
                                prompt,
                                aspect_ratio,
                                headers,
                                image_bytes,
                                image_mime,
                                mask_bytes,
                                mask_mime,
                                extra_args,
                            )
                    except Exception as exc:
                        errors.append(f"{label}: {exc}")
                        continue
                    if has_image(result):
                        elapsed = time.monotonic() - started
                        info = _info_header(
                            tag,
                            response_id,
                            elapsed,
                            retries_used,
                            flags,
                        )
                        if info:
                            result.content.insert(0, text_content(info))
                        return result
                    errors.append(f"{label}: {result_text(result)}")
    except Exception as exc:
        return error_result(f"Image {kind} request failed: {exc}")

    return error_result(f"All attempts failed for {tag}:\n" + "\n".join(errors))


async def generate_image(
    config: Any,
    prompt: str,
    aspect_ratio: str = "",
    model_tag: str = "",
    extra_args: dict[str, Any] | None = None,
) -> mcp_types.CallToolResult:
    """Generate images by walking the ordered source/model plan.

    Args:
        config: The plugin configuration mapping.
        prompt: The prompt text.
        aspect_ratio: The aspect ratio or size to send, when validated.
        model_tag: Restrict the plan to one source/model tag.
        extra_args: Extra request body fields appended verbatim.

    Returns:
        The first result carrying an image, or a combined error result.
    """
    plan = model_plan(config, "generation", model_tag)
    if not plan:
        return error_result("No enabled image generation source is configured.")

    errors: list[str] = []
    for plan_item in plan:
        suffixed = prompt_for(config, plan_item["source"], "generation", prompt)
        result = await _execute_plan_item(
            config,
            plan_item,
            "generation",
            suffixed,
            aspect_ratio=aspect_ratio,
            extra_args=extra_args,
        )
        if has_image(result):
            return result
        errors.append(result_text(result))
    return error_result(
        "All image generation sources failed:\n" + "\n".join(errors),
    )


async def edit_image(
    config: Any,
    prompt: str,
    image: str,
    mask: str = "",
    aspect_ratio: str = "",
    model_tag: str = "",
    extra_args: dict[str, Any] | None = None,
) -> mcp_types.CallToolResult:
    """Edit images by walking the ordered source/model plan.

    Args:
        config: The plugin configuration mapping.
        prompt: The prompt text.
        image: The source image as a URL, data URI, or base64 string.
        mask: An optional mask image.
        aspect_ratio: The aspect ratio or size to send, when validated.
        model_tag: Restrict the plan to one source/model tag.
        extra_args: Extra multipart fields appended verbatim.

    Returns:
        The first result carrying an image, or a combined error result.
    """
    plan = model_plan(config, "edit", model_tag)
    if not plan:
        return error_result("No enabled image edit source is configured.")

    errors: list[str] = []
    for plan_item in plan:
        suffixed = prompt_for(config, plan_item["source"], "edit", prompt)
        result = await _execute_plan_item(
            config,
            plan_item,
            "edit",
            suffixed,
            aspect_ratio=aspect_ratio,
            image=image,
            mask=mask,
            extra_args=extra_args,
        )
        if has_image(result):
            return result
        errors.append(result_text(result))
    return error_result(
        "All image edit sources failed:\n" + "\n".join(errors),
    )


async def polish_prompt(
    provider: Any,
    prompt: str,
) -> mcp_types.CallToolResult:
    """Polish a rough prompt using the current chat model provider."""
    try:
        response = await provider.text_chat(
            prompt=prompt,
            system_prompt=POLISH_SYSTEM_PROMPT,
        )
        polished = (response.completion_text or "").strip()
        if not polished:
            return error_result("The model returned an empty polished prompt.")
        return mcp_types.CallToolResult(
            content=[text_content(f"Polished prompt:\n{polished}")],
        )
    except Exception as exc:
        return error_result(f"Prompt polishing failed: {exc}")
