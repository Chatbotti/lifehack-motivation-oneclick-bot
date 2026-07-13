#!/usr/bin/env python3
"""Register the Render webhook URL with Telegram."""

from __future__ import annotations

import os
import re
import sys

from telegram_api import api_call


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is empty.")
    return value


def main() -> int:
    try:
        token = require_env("TELEGRAM_BOT_TOKEN")
        base_url = require_env("PUBLIC_BASE_URL").rstrip("/")
        secret = require_env("WEBHOOK_SECRET")

        if not base_url.startswith("https://"):
            raise RuntimeError("PUBLIC_BASE_URL must begin with https://")
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,256}", secret):
            raise RuntimeError(
                "WEBHOOK_SECRET must be 16-256 characters using letters, "
                "numbers, underscore, or hyphen only."
            )

        webhook_url = f"{base_url}/telegram/{secret}"
        result = api_call(
            token,
            "setWebhook",
            url=webhook_url,
            secret_token=secret,
            allowed_updates=["message"],
            drop_pending_updates=False,
        )
        print(result["description"])
        print(f"Webhook registered for: {base_url}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
