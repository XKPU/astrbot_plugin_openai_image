"""Chat command parsing for the image generation and editing commands."""

from __future__ import annotations

from typing import Any

from .response_utils import result_text

DEFAULT_PREFIX = "/"
DEFAULT_GENERATION_HEADS = ("t2i",)
DEFAULT_EDIT_HEADS = ("i2i",)
DEFAULT_ALLOWED_ARGS = ("size",)
ARG_MODES = ("off", "all", "listed")


def head_list(value: Any, defaults: tuple[str, ...]) -> list[str]:
    """Normalize a configured command head list.

    A plain string is accepted for configurations written before multiple
    heads were supported; entries are separated by commas or newlines.
    """
    if isinstance(value, str):
        value = value.replace(",", "\n").splitlines()
    if not isinstance(value, list):
        return list(defaults)
    heads: list[str] = []
    for entry in value:
        head = str(entry).strip()
        if head and head.lower() not in {item.lower() for item in heads}:
            heads.append(head)
    return heads or list(defaults)


def _name_list(value: Any) -> list[str]:
    """Normalize a list of argument names (strings or comma/newline lists).

    A missing setting falls back to the default names; an explicitly empty
    list means no argument is accepted.
    """
    if value is None:
        return list(DEFAULT_ALLOWED_ARGS)
    if isinstance(value, str):
        value = value.replace(",", "\n").splitlines()
    if not isinstance(value, list):
        return list(DEFAULT_ALLOWED_ARGS)
    names: list[str] = []
    for entry in value:
        name = str(entry).strip().lower()
        if name and name not in names:
            names.append(name)
    return names


def command_settings(config: Any) -> dict[str, Any]:
    """Read the command switches from the plugin configuration.

    Args:
        config: The plugin configuration mapping.

    Returns:
        A dict with enabled, prefix, generation_heads, edit_heads, polish,
        polish_provider, arg_mode and allowed_args entries.
    """
    mode = str(config.get("command_arg_mode") or "").strip().lower()
    return {
        "enabled": bool(config.get("enable_commands", True)),
        "prefix": str(config.get("command_prefix") or "").strip() or DEFAULT_PREFIX,
        "generation_heads": head_list(
            config.get("command_generation_head"),
            DEFAULT_GENERATION_HEADS,
        ),
        "edit_heads": head_list(
            config.get("command_edit_head"),
            DEFAULT_EDIT_HEADS,
        ),
        "polish": bool(config.get("command_enable_polish", False)),
        "polish_provider": str(config.get("command_polish_provider") or "").strip(),
        "arg_mode": mode if mode in ARG_MODES else "listed",
        "allowed_args": _name_list(config.get("command_allowed_args")),
    }


def _key_end(text: str, start: int) -> int:
    """Return the end offset of a run of argument key characters."""
    cursor = start
    while cursor < len(text) and (text[cursor].isalnum() or text[cursor] in "_-."):
        cursor += 1
    return cursor


def arg_start(text: str) -> int:
    """Return the offset of the first ``--key:value`` argument, or -1."""
    position = 0
    while True:
        index = text.find("--", position)
        if index < 0:
            return -1
        end = _key_end(text, index + 2)
        boundary = index == 0 or text[index - 1].isspace()
        if boundary and end > index + 2 and text[end : end + 1] == ":":
            return index
        position = index + 2


def _arg_chunks(region: str) -> list[str]:
    """Split an argument region into ``key:value`` chunks."""
    bounds: list[int] = []
    position = 0
    while True:
        index = region.find("--", position)
        if index < 0:
            break
        if index == 0 or region[index - 1].isspace():
            bounds.append(index)
        position = index + 2
    chunks: list[str] = []
    for order, start in enumerate(bounds):
        end = bounds[order + 1] if order + 1 < len(bounds) else len(region)
        chunk = region[start + 2 : end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _clean_value(value: str) -> Any:
    """Coerce an argument value into a bool, number, or string."""
    value = value.strip()
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            continue
    return value


def split_prompt_args(
    text: str,
    allowed: list[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Split text into the prompt and the trailing ``--key:value`` arguments.

    Any ``--key:value`` ends the prompt, even when its name is not allowed; an
    unlisted argument is simply not forwarded to the request.

    Args:
        text: The command body after the command head.
        allowed: When given, only these argument names are forwarded.

    Returns:
        The prompt text and the extra request arguments.
    """
    index = arg_start(text)
    if index < 0:
        return text.strip(), {}
    args: dict[str, Any] = {}
    for chunk in _arg_chunks(text[index:]):
        key, separator, value = chunk.partition(":")
        key = key.strip()
        if not key:
            continue
        if allowed is not None and key.lower() not in allowed:
            continue
        args[key] = _clean_value(value) if separator else True
    return text[:index].strip(), args


def _head_body(body: str, head: str) -> str | None:
    """Return the text after a matching command head, else None."""
    if not head or body[: len(head)].lower() != head.lower():
        return None
    rest = body[len(head) :]
    if rest and not rest[0].isspace():
        return None
    return rest.strip()


def command_body(text: str, prefix: str, woken: bool) -> str | None:
    """Strip the configured prefix and return the command body.

    Args:
        text: Raw message text; the server may already have stripped its own
            wake prefix.
        prefix: The configured command wake prefix.
        woken: Whether the message was woken by prefix, at-mention or private
            chat.

    Returns:
        The text after the prefix, or None when the message is not woken.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    if prefix and raw.startswith(prefix):
        return raw[len(prefix) :].strip()
    if not woken:
        return None
    return raw


def parse_checkin(
    text: str,
    settings: dict[str, Any],
    woken: bool,
) -> str | None:
    """Match a check-in command head.

    Args:
        text: Raw message text.
        settings: The result of :func:`command_settings` merged with the
            check-in heads.
        woken: Whether the message was woken by prefix, at-mention or private
            chat.

    Returns:
        The matched head, or None when the message is not a check-in command.
    """
    body = command_body(text, settings["prefix"], woken)
    if not body:
        return None
    for head in settings.get("checkin_heads") or []:
        if _head_body(body, head) is not None:
            return head
    return None


def parse_command(
    text: str,
    settings: dict[str, Any],
    woken: bool,
) -> dict[str, Any] | None:
    """Parse a chat message into a command, or None when it is not one.

    Args:
        text: Raw message text; the server may already have stripped its own
            wake prefix.
        settings: The result of :func:`command_settings`.
        woken: Whether the message was woken by prefix, at-mention or private
            chat. Only used when the configured prefix is absent from the text.

    Returns:
        A dict with kind ("generation" or "edit"), prompt and args, or None.
    """
    raw = command_body(text, settings["prefix"], woken)
    if not raw:
        return None
    candidates = [(head, "generation") for head in settings["generation_heads"]] + [
        (head, "edit") for head in settings["edit_heads"]
    ]
    # Longest head first so that overlapping heads match the most specific one.
    for head, kind in sorted(candidates, key=lambda item: len(item[0]), reverse=True):
        rest = _head_body(raw, head)
        if rest is None:
            continue
        mode = settings.get("arg_mode", "listed")
        if mode == "off":
            return {"kind": kind, "prompt": rest, "args": {}}
        allowed = settings.get("allowed_args") if mode == "listed" else None
        prompt, args = split_prompt_args(rest, allowed)
        return {"kind": kind, "prompt": prompt, "args": args}
    return None


def result_payload(result: Any) -> tuple[str, list[str]]:
    """Split a tool result into a chat note and base64 image payloads.

    Args:
        result: A ``CallToolResult`` returned by the request layer.

    Returns:
        The remaining text (errors and optional info headers) and the base64
        payload of every image block.
    """
    notes = [
        line
        for line in result_text(result).splitlines()
        if line.strip() and not line.startswith(("Returned ", "Image "))
    ]
    images = [
        item.data for item in result.content if getattr(item, "type", None) == "image"
    ]
    return "\n".join(notes), images
