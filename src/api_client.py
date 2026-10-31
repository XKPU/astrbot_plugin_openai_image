"""HTTP request layer for OpenAI-compatible image APIs."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import aiohttp
from mcp import types as mcp_types

from astrbot.api import logger

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
from .reference_images import download_image
from .response_utils import (
    error_result,
    extract_images,
    failure,
    guess_mime,
    has_image,
    image_content,
    result_text,
    split_image_value,
    text_content,
)

# Chat-facing failure text per request kind; details stay in the log only.
_REQUEST_FAILURE = {
    "generation": "图像生成失败，请稍后重试或联系管理员查看日志。",
    "edit": "图像编辑失败，请稍后重试或联系管理员查看日志。",
}


async def fetch_bytes(url: str, allow_any_port: bool = False) -> tuple[bytes, str]:
    """Download a remote image through the guarded downloader.

    Args:
        url: The image URL returned by the API.
        allow_any_port: Accept the URL on any public port. Image URLs returned by
            the configured API may live on its own gateway port; every other
            guard (public address, size, format, time) still applies.

    Returns:
        A tuple of (bytes, mime).

    Raises:
        ReferenceImageError: The URL is not a public HTTP(S) image or it fails
            the size, format or time limits.
    """
    body = await download_image(url, allow_any_port)
    return body, guess_mime(base64.b64encode(body).decode())


async def load_image_data_url(value: str) -> str:
    """Load one reference image and return it as a base64 data URL.

    The JSON edit API takes ``ImageRefParam`` entries whose ``image_url`` is a
    fully qualified URL or a base64 data URL. Remote URLs are downloaded here
    and re-encoded, because several OpenAI-compatible routers refuse to fetch
    them on their own.
    """
    kind, data, mime = split_image_value(value)
    if kind == "url":
        body, mime = await fetch_bytes(data)
        data = base64.b64encode(body).decode()
    return f"data:{mime or guess_mime(data)};base64,{data}"


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
    response: aiohttp.ClientResponse,
    response_image_path: str,
) -> tuple[mcp_types.CallToolResult, str]:
    """Turn an image API response into (tool result, response id)."""
    text = await response.text()
    if response.status < 200 or response.status >= 300:
        return failure(
            "图像接口请求失败，请稍后重试。",
            f"HTTP {response.status}: {text[:2000]}",
        ), ""
    try:
        payload: Any = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return failure(
            "图像接口返回了无法解析的内容。",
            f"non-JSON response: {text[:2000]}",
        ), ""
    response_id = ""
    if isinstance(payload, dict):
        response_id = str(payload.get("id") or "")

    image_values = extract_images(payload, response_image_path)
    if not image_values:
        return failure(
            "未在接口响应中找到图片。",
            f"response field '{response_image_path}': {text[:2000]}",
        ), response_id

    content: list[mcp_types.ContentBlock] = []
    notes: list[str] = [f"Returned {len(image_values)} image(s)."]
    for index, value in enumerate(image_values, start=1):
        kind, data, mime = split_image_value(value)
        if kind == "url":
            notes.append(f"Image {index} URL: {data}")
            try:
                # The configured API may serve images from its own gateway
                # port, so the port allowlist is relaxed here; internal
                # addresses, size, format and time limits still apply.
                body, mime = await fetch_bytes(data, allow_any_port=True)
            except Exception as exc:
                logger.warning("openai_image: image URL download failed: %r", exc)
                notes.append(
                    f"Image {index} could not be downloaded. "
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
    images: list[str],
    mask: str,
    extra_args: dict[str, Any] | None = None,
) -> mcp_types.CallToolResult:
    """Send one JSON edit request and normalize the response.

    The edit endpoint takes the ``images`` array of ``ImageRefParam`` objects,
    each holding a base64 data URL in ``image_url``; ``mask`` uses the same
    shape. Multipart uploads are not used, because several OpenAI-compatible
    routers only accept the JSON form.
    """
    payload = merged_extra(config, source)
    field = source["aspect_ratio_field"] or ratio_field(config)
    payload["model"] = model_id
    payload["prompt"] = prompt
    if aspect_ratio:
        payload[field] = aspect_ratio
    payload["images"] = [{"image_url": value} for value in images]
    if mask:
        payload["mask"] = {"image_url": mask}
    if extra_args:
        payload.update(extra_args)

    # Per-source override wins over the global response_image_path.
    response_path = str(
        source.get("response_image_path") or config.get("response_image_path") or "data"
    )
    headers["Content-Type"] = "application/json"
    async with session.post(
        f"{source['api_base']}/images/edits",
        headers=headers,
        json=payload,
    ) as response:
        return await handle_response(response, response_path)


async def _execute_plan_item(
    config: Any,
    plan_item: dict[str, Any],
    kind: str,
    prompt: str,
    aspect_ratio: str = "",
    images: list[str] | None = None,
    mask: str = "",
    extra_args: dict[str, Any] | None = None,
    gate: Any = None,
) -> mcp_types.CallToolResult:
    """Run one plan item (source + model): keys x retries, then the request.

    kind is "generation" (JSON POST /images/generations) or "edit" (JSON POST
    /images/edits). Returns the first result carrying an image; failure notes
    are accumulated otherwise. extra_args are appended verbatim to the request
    body (command arguments). gate, when given, charges one daily call before
    every real request and aborts the remaining attempts once the quota is
    exhausted.
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
            data_urls: list[str] = []
            mask_url = ""
            if kind == "edit":
                data_urls = [
                    await load_image_data_url(value) for value in (images or [])
                ]
                if mask.strip():
                    mask_url = await load_image_data_url(mask)

            for key_index, api_key in enumerate(source["api_keys"], start=1):
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                label = f"{tag} key {key_index}"
                for attempt in range(attempts):
                    if attempt:
                        retries_used += 1
                    if gate is not None:
                        denial = gate.charge()
                        if denial:
                            return error_result(denial)
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
                                data_urls,
                                mask_url,
                                extra_args,
                            )
                    except Exception as exc:
                        errors.append(f"{label}: {exc!r}")
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
        return failure(_REQUEST_FAILURE[kind], f"{kind}: {exc!r}")

    return failure(_REQUEST_FAILURE[kind], " | ".join(errors))


async def generate_image(
    config: Any,
    prompt: str,
    aspect_ratio: str = "",
    model_tag: str = "",
    extra_args: dict[str, Any] | None = None,
    gate: Any = None,
) -> mcp_types.CallToolResult:
    """Generate images by walking the ordered source/model plan.

    Args:
        config: The plugin configuration mapping.
        prompt: The prompt text.
        aspect_ratio: The aspect ratio or size to send, when validated.
        model_tag: Restrict the plan to one source/model tag.
        extra_args: Extra request body fields appended verbatim.
        gate: Optional quota gate charged once per real request.

    Returns:
        The first result carrying an image, or a combined error result.
    """
    plan = model_plan(config, "generation", model_tag)
    if not plan:
        return failure("没有可用的图像生成来源，请联系管理员检查配置。")

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
            gate=gate,
        )
        if has_image(result):
            return result
        if gate is not None and gate.exhausted:
            return result
        errors.append(result_text(result))
    return failure(_REQUEST_FAILURE["generation"], " | ".join(errors))


async def edit_image(
    config: Any,
    prompt: str,
    images: list[str],
    mask: str = "",
    aspect_ratio: str = "",
    model_tag: str = "",
    extra_args: dict[str, Any] | None = None,
    gate: Any = None,
) -> mcp_types.CallToolResult:
    """Edit images by walking the ordered source/model plan.

    Args:
        config: The plugin configuration mapping.
        prompt: The prompt text.
        images: One or more source images, each a URL, data URI, or base64
            string. They are sent as an ``images`` array of ``image_url`` data
            URLs, as the OpenAI edit endpoint requires.
        mask: An optional mask image.
        aspect_ratio: The aspect ratio or size to send, when validated.
        model_tag: Restrict the plan to one source/model tag.
        extra_args: Extra request body fields appended verbatim.
        gate: Optional quota gate charged once per real request.

    Returns:
        The first result carrying an image, or a combined error result.
    """
    plan = model_plan(config, "edit", model_tag)
    if not plan:
        return failure("没有可用的图像编辑来源，请联系管理员检查配置。")

    errors: list[str] = []
    for plan_item in plan:
        suffixed = prompt_for(config, plan_item["source"], "edit", prompt)
        result = await _execute_plan_item(
            config,
            plan_item,
            "edit",
            suffixed,
            aspect_ratio=aspect_ratio,
            images=images,
            mask=mask,
            extra_args=extra_args,
            gate=gate,
        )
        if has_image(result):
            return result
        if gate is not None and gate.exhausted:
            return result
        errors.append(result_text(result))
    return failure(_REQUEST_FAILURE["edit"], " | ".join(errors))


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
            return failure("提示词润色失败，请稍后重试。", "empty model response")
        return mcp_types.CallToolResult(
            content=[text_content(f"Polished prompt:\n{polished}")],
        )
    except Exception as exc:
        return failure("提示词润色失败，请稍后重试。", f"polish error: {exc!r}")
