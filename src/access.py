"""Region black/white lists, daily quotas and check-in rewards."""

from __future__ import annotations

import json
import os
import threading
from datetime import date
from pathlib import Path
from typing import Any

from astrbot.api import logger

from .commands import head_list

DENY_MESSAGE = "当前会话或用户无权使用此功能。"
CHECKIN_DISABLED_MESSAGE = "签到功能未启用。"
DEFAULT_CHECKIN_HEADS = ("checkin",)
DEFAULT_CHECKIN_SUCCESS = (
    "签到成功，获得 {{count}} 次调用次数，今日剩余 {{remaining}} 次。"
)
DEFAULT_CHECKIN_FAIL = "今天已经签到过了，明天再来吧。"
MODES = ("off", "whitelist", "blacklist")


def _id_list(value: Any) -> list[str]:
    """Normalize a configured id list (accepts a string or a list)."""
    if isinstance(value, str):
        value = value.replace(",", "\n").splitlines()
    if not isinstance(value, list):
        return []
    ids: list[str] = []
    for entry in value:
        item = str(entry).strip()
        if item and item not in ids:
            ids.append(item)
    return ids


def _mode(value: Any) -> str:
    """Normalize a list mode, falling back to the unrestricted mode."""
    mode = str(value or "").strip().lower()
    return mode if mode in MODES else "off"


def access_settings(config: Any) -> dict[str, Any]:
    """Read the access-control settings from the plugin configuration.

    Args:
        config: The plugin configuration mapping.

    Returns:
        A dict with group/user list modes and ids, the daily limit and the
        check-in switches, bonus and reply templates.
    """
    return {
        "group_mode": _mode(config.get("access_group_mode")),
        "group_ids": _id_list(config.get("access_group_ids")),
        "user_mode": _mode(config.get("access_user_mode")),
        "user_ids": _id_list(config.get("access_user_ids")),
        "daily_limit": max(int(config.get("quota_daily_limit") or 0), 0),
        "checkin_enabled": bool(config.get("checkin_enabled", False)),
        "checkin_heads": head_list(config.get("checkin_heads"), DEFAULT_CHECKIN_HEADS),
        "checkin_bonus": max(int(config.get("checkin_bonus") or 0), 0),
        "checkin_success": str(
            config.get("checkin_success") or DEFAULT_CHECKIN_SUCCESS,
        ),
        "checkin_fail": str(config.get("checkin_fail") or DEFAULT_CHECKIN_FAIL),
    }


def verdict(settings: dict[str, Any], group_id: str, user_id: str) -> str:
    """Check the black/white lists for the current chat and sender.

    Args:
        settings: The result of :func:`access_settings`.
        group_id: The group id, empty in private chats.
        user_id: The sender key.

    Returns:
        An empty string when allowed, otherwise the denial message.
    """
    if group_id:
        listed = group_id in settings["group_ids"]
        if settings["group_mode"] == "whitelist" and not listed:
            return DENY_MESSAGE
        if settings["group_mode"] == "blacklist" and listed:
            return DENY_MESSAGE
    listed = user_id in settings["user_ids"]
    if settings["user_mode"] == "whitelist" and not listed:
        return DENY_MESSAGE
    if settings["user_mode"] == "blacklist" and listed:
        return DENY_MESSAGE
    return ""


def quota_message(used: int, limit: int) -> str:
    """Build the reply sent when the daily quota is exhausted."""
    return f"今日调用次数已用完（已用 {used} 次，上限 {limit} 次），请明天再试。"


def render(template: str, count: int, remaining: int, limit: int) -> str:
    """Fill the check-in reply placeholders.

    Args:
        template: The configured reply template.
        count: Attempts granted by this check-in.
        remaining: Attempts left today; -1 means the quota is unlimited.
        limit: The daily limit; 0 means unlimited.

    Returns:
        The rendered reply text.
    """
    left = "不限" if limit <= 0 else str(max(remaining, 0))
    return (
        template.replace("{{count}}", str(count))
        .replace("{{remaining}}", left)
        .replace("{{limit}}", "不限" if limit <= 0 else str(limit))
    )


class QuotaStore:
    """Daily usage counters and check-in state stored in one JSON file.

    Counters are scoped per sender and reset when the local date changes.
    Writes are atomic so an interrupted save cannot truncate the file.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        """Load today's counters, dropping data from previous days."""
        data: Any = {}
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            data = {}
        today = date.today().isoformat()
        if not isinstance(data, dict) or data.get("date") != today:
            return {"date": today, "users": {}}
        users = data.get("users")
        return {"date": today, "users": users if isinstance(users, dict) else {}}

    def _write(self, data: dict[str, Any]) -> None:
        """Persist the counters through a temporary file."""
        temp = self._path.with_suffix(".tmp")
        try:
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            os.replace(temp, self._path)
        except OSError as exc:
            logger.warning("Failed to save usage data: %s", exc)

    def _record(self, data: dict[str, Any], user_key: str) -> dict[str, Any]:
        """Return the mutable counter record of a sender."""
        record = data["users"].get(user_key)
        if not isinstance(record, dict):
            record = {}
        record["used"] = max(int(record.get("used") or 0), 0)
        record["bonus"] = max(int(record.get("bonus") or 0), 0)
        record["checked"] = bool(record.get("checked"))
        return record

    def usage(self, user_key: str, daily_limit: int) -> tuple[int, int]:
        """Return the used count and the effective limit (0 = unlimited)."""
        with self._lock:
            record = self._record(self._read(), user_key)
        limit = daily_limit + record["bonus"] if daily_limit > 0 else 0
        return record["used"], limit

    def consume(self, user_key: str, daily_limit: int) -> bool:
        """Claim one call for the sender.

        Args:
            user_key: The sender key.
            daily_limit: The configured limit; 0 disables the quota.

        Returns:
            True when a call was claimed, False when the quota is exhausted.
        """
        with self._lock:
            data = self._read()
            record = self._record(data, user_key)
            limit = daily_limit + record["bonus"] if daily_limit > 0 else 0
            if limit > 0 and record["used"] >= limit:
                return False
            record["used"] += 1
            data["users"][user_key] = record
            self._write(data)
            return True

    def checkin(
        self,
        user_key: str,
        bonus_gain: int,
        daily_limit: int,
    ) -> tuple[bool, int, int]:
        """Record a check-in and grant the bonus.

        Args:
            user_key: The sender key.
            bonus_gain: Attempts granted by this check-in.
            daily_limit: The configured limit; 0 disables the quota.

        Returns:
            A tuple of (checked now, attempts granted, attempts remaining).
            Remaining is -1 when the quota is unlimited.
        """
        with self._lock:
            data = self._read()
            record = self._record(data, user_key)
            limit = daily_limit + record["bonus"] if daily_limit > 0 else 0
            remaining = max(limit - record["used"], 0) if limit > 0 else -1
            if record["checked"]:
                return False, 0, remaining
            record["bonus"] += max(bonus_gain, 0)
            record["checked"] = True
            data["users"][user_key] = record
            self._write(data)
            limit = daily_limit + record["bonus"] if daily_limit > 0 else 0
            remaining = max(limit - record["used"], 0) if limit > 0 else -1
            return True, max(bonus_gain, 0), remaining
