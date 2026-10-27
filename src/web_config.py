"""Web API helpers exposing config read/write for the config view."""

from __future__ import annotations

import json
from typing import Any

from astrbot.api import logger

from .constants import TEMPLATE_KEY


def ensure_template_keys(config: dict[str, Any]) -> bool:
    """Stamp the template key on every source entry.

    The declarative settings page rejects template_list entries without
    one, so stamping keeps both config pages in sync.

    Returns True when the config was modified and needs persisting.
    """
    changed = False
    for item in config.get("sources") or []:
        if isinstance(item, dict) and item.get("__template_key") != TEMPLATE_KEY:
            item["__template_key"] = TEMPLATE_KEY
            changed = True
    return changed


def parse_json_body(raw: bytes | str) -> dict[str, Any] | None:
    """Parse a JSON request body, returning None on failure."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def log_config_update(username: str | None) -> None:
    """Log a config update for auditing."""
    logger.info(
        "openai_image config updated via WebUI by %s",
        username or "unknown",
    )
