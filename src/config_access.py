"""Config accessors and payload builders for the OpenAI image plugin."""

from __future__ import annotations

from typing import Any

import aiohttp

DEFAULT_RATIO_FIELD = "size"
DEFAULT_TIMEOUT = 300


def _split_list(value: Any) -> list[str]:
    """Split a comma/newline separated string or list into cleaned items."""
    if isinstance(value, str):
        value = value.replace(",", "\n").splitlines()
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for entry in value:
        item = str(entry).strip()
        if item and item not in items:
            items.append(item)
    return items


def _parse_model_entry(entry: Any) -> tuple[str, int] | None:
    """Parse a model entry into (model_id, retries).

    Accepts "model_id", "model_id:retries", or {"id": ..., "retries": ...}.
    """
    if isinstance(entry, dict):
        model_id = str(
            entry.get("id") or entry.get("model") or entry.get("name") or ""
        ).strip()
        try:
            retries = int(entry.get("retries", 0) or 0)
        except (TypeError, ValueError):
            retries = 0
    else:
        text = str(entry).strip()
        if not text:
            return None
        model_id, _, retry_part = text.partition(":")
        model_id = model_id.strip()
        try:
            retries = int(retry_part.strip() or 0)
        except ValueError:
            retries = 0
    if not model_id:
        return None
    return model_id, max(retries, 0)


def available_aspect_ratios(config: Any) -> list[str]:
    """Parse the global aspect ratio options into a deduplicated list."""
    return _split_list(config.get("available_aspect_ratios"))


def ratio_field(config: Any) -> str:
    """Return the global request field name that receives the aspect ratio."""
    return str(config.get("aspect_ratio_field") or DEFAULT_RATIO_FIELD).strip()


def sources(config: Any) -> list[dict[str, Any]]:
    """Resolve enabled sources and their models from the new-format config."""
    raw = config.get("sources")
    if not isinstance(raw, list):
        return []
    resolved: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("enabled", True):
            continue
        api_base = str(item.get("api_base") or "").strip().rstrip("/")
        if not api_base:
            continue
        keys = item.get("api_keys") or []
        if isinstance(keys, str):
            keys = keys.replace(",", "\n").splitlines()
        api_keys = [str(key).strip() for key in keys if str(key).strip()] or [""]
        models: list[dict[str, Any]] = []
        for entry in item.get("models") or []:
            parsed = _parse_model_entry(entry)
            if parsed:
                models.append({"id": parsed[0], "retries": parsed[1]})
        if not models and item.get("model"):
            # Fallback: accept a single "model" value for backward compatibility.
            parsed = _parse_model_entry(item["model"])
            if parsed:
                models.append({"id": parsed[0], "retries": parsed[1]})
        if not models:
            continue
        extra = item.get("extra_request_body")
        try:
            source_timeout = float(item.get("timeout") or 0)
        except (TypeError, ValueError):
            source_timeout = 0
        resolved.append(
            {
                "name": str(item.get("name") or api_base).strip() or api_base,
                "api_base": api_base,
                "api_keys": api_keys,
                "models": models,
                "enable_generation": bool(item.get("enable_generation", True)),
                "enable_edit": bool(item.get("enable_edit", True)),
                "aspect_ratios": _split_list(item.get("aspect_ratios")) or None,
                "aspect_ratio_field": (
                    str(item.get("aspect_ratio_field") or "").strip() or None
                ),
                "validate_aspect_ratio": bool(
                    item.get("validate_aspect_ratio", True),
                ),
                "generation_prompt": (
                    str(item.get("generation_prompt") or "").strip() or None
                ),
                "edit_prompt": str(item.get("edit_prompt") or "").strip() or None,
                "extra_request_body": extra if isinstance(extra, dict) else {},
                "timeout": source_timeout if source_timeout > 0 else None,
                "response_image_path": (
                    str(item.get("response_image_path") or "").strip() or None
                ),
            },
        )
    return resolved


def _applied_model_order(config: Any) -> list[str]:
    """Normalize the global model_order list into ordered tag patterns."""
    patterns: list[str] = []
    for entry in config.get("model_order") or []:
        if isinstance(entry, dict):
            entry = entry.get("tag") or entry.get("id") or ""
        pattern = str(entry).strip()
        if pattern and pattern not in patterns:
            patterns.append(pattern)
    return patterns


def _apply_model_order(
    plan: list[dict[str, Any]],
    patterns: list[str],
) -> list[dict[str, Any]]:
    """Reorder plan items following the global model_order patterns.

    Patterns listed in model_order come first (in that order), matched by
    exact tag or "/model_id" suffix; unlisted items keep their relative
    order at the end.
    """
    if not patterns:
        return plan

    def rank(item: dict[str, Any]) -> int:
        tag = item["tag"]
        for index, pattern in enumerate(patterns):
            if tag == pattern or tag.endswith("/" + pattern):
                return index
        return len(patterns)

    return sorted(plan, key=rank)


def model_plan(
    config: Any,
    capability: str,
    model_tag: str = "",
) -> list[dict[str, Any]]:
    """Build the ordered execution plan of (source, model) pairs.

    Each plan item: {source, model, retries, tag} where tag is
    "{source_name}/{model_id}". The global model_order list reorders the
    plan; with model_tag given, only matching items are kept (exact tag
    first, then by model id suffix).
    """
    plan: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in sources(config):
        if capability == "generation" and not source["enable_generation"]:
            continue
        if capability == "edit" and not source["enable_edit"]:
            continue
        for model in source["models"]:
            key = (source["name"], model["id"])
            if key in seen:
                continue
            seen.add(key)
            plan.append(
                {
                    "source": source,
                    "model": model["id"],
                    "retries": model["retries"],
                    "tag": f"{source['name']}/{model['id']}",
                },
            )
    plan = _apply_model_order(plan, _applied_model_order(config))
    if model_tag.strip():
        wanted = model_tag.strip()
        matched = [item for item in plan if item["tag"] == wanted]
        if not matched:
            model_id = wanted.split("/", 1)[-1].strip()
            matched = [
                item
                for item in plan
                if item["model"] == model_id or item["tag"].endswith("/" + model_id)
            ]
        plan = matched
    return plan


def model_tags(config: Any, capability: str) -> list[str]:
    """Return the deduplicated source/model tags available for a capability."""
    return [item["tag"] for item in model_plan(config, capability)]


def ratio_options(config: Any, capability: str) -> list[str]:
    """Union of aspect ratio options across the ratio-validating sources."""
    options: list[str] = []
    fallback = available_aspect_ratios(config)
    for item in model_plan(config, capability):
        source = item["source"]
        if not source["validate_aspect_ratio"]:
            continue
        for ratio in source["aspect_ratios"] or fallback:
            if ratio not in options:
                options.append(ratio)
    return options


def free_ratio(config: Any, capability: str) -> bool:
    """True when any participating source disables aspect ratio validation."""
    return any(
        not item["source"]["validate_aspect_ratio"]
        for item in model_plan(config, capability)
    )


def prompt_for(config: Any, source: dict[str, Any], kind: str, prompt: str) -> str:
    """Append the {kind}_prompt suffix (source override first, then global)."""
    suffix = (
        source.get(f"{kind}_prompt") or str(config.get(f"{kind}_prompt") or "").strip()
    )
    return f"{prompt}\n\n{suffix}" if suffix else prompt


def merged_extra(config: Any, source: dict[str, Any]) -> dict[str, Any]:
    """Merge global and per-source extra request body (source wins)."""
    extra = config.get("extra_request_body")
    merged = dict(extra) if isinstance(extra, dict) else {}
    merged.update(source.get("extra_request_body") or {})
    return merged


def generation_payload(
    config: Any,
    source: dict[str, Any],
    model_id: str,
    prompt: str,
    aspect_ratio: str = "",
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the JSON body for an image generation request.

    Args:
        config: The plugin configuration mapping.
        source: The resolved source entry.
        model_id: The model id to request.
        prompt: The prompt text.
        aspect_ratio: The aspect ratio or size to send, when validated.
        extra_args: Command line arguments appended verbatim to the body.

    Returns:
        The JSON request body.
    """
    payload = merged_extra(config, source)
    payload["model"] = model_id
    payload["prompt"] = prompt
    if aspect_ratio:
        field = source["aspect_ratio_field"] or ratio_field(config)
        payload[field] = aspect_ratio
    if extra_args:
        payload.update(extra_args)
    return payload


def request_timeout(
    config: Any,
    source: dict[str, Any] | None = None,
) -> aiohttp.ClientTimeout:
    """Build the aiohttp timeout (per-source override, else global)."""
    seconds = DEFAULT_TIMEOUT
    if source and source.get("timeout"):
        seconds = source["timeout"]
    else:
        try:
            seconds = float(config.get("timeout", DEFAULT_TIMEOUT))
        except (TypeError, ValueError):
            seconds = DEFAULT_TIMEOUT
    return aiohttp.ClientTimeout(total=max(seconds, 1))


def return_info_flags(config: Any) -> dict[str, bool]:
    """Read the tool-result info switches (elapsed / id / model / retries)."""
    return {
        "elapsed": bool(config.get("return_elapsed", False)),
        "id": bool(config.get("return_id", False)),
        "model": bool(config.get("return_model", False)),
        "retries": bool(config.get("return_retries", False)),
    }
