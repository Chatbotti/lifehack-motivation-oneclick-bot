"""Small dependency-free helpers for the Telegram Bot API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class TelegramError(RuntimeError):
    pass


def _request_json(url: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded = None
    if data is not None:
        encoded = urllib.parse.urlencode(data).encode("utf-8")

    request = urllib.request.Request(url, data=encoded)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise TelegramError(f"Telegram HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise TelegramError(f"Could not reach Telegram: {exc.reason}") from exc

    result = json.loads(body)
    if not result.get("ok"):
        raise TelegramError(f"Telegram API error: {result}")
    return result


def api_call(token: str, method: str, **params: Any) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    normalized: dict[str, Any] = {}

    for key, value in params.items():
        if isinstance(value, (list, dict, bool)):
            normalized[key] = json.dumps(value)
        else:
            normalized[key] = value

    return _request_json(url, normalized)


def send_message(token: str, chat_id: str | int, text: str) -> None:
    api_call(
        token,
        "sendMessage",
        chat_id=str(chat_id),
        text=text,
        disable_web_page_preview=True,
    )


def download_text_document(
    token: str,
    file_id: str,
    *,
    max_download_bytes: int = 250_000,
) -> str:
    metadata = api_call(token, "getFile", file_id=file_id)
    file_path = metadata["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"

    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            raw = response.read(max_download_bytes + 1)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise TelegramError(f"Telegram file HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise TelegramError(f"Could not download Telegram file: {exc.reason}") from exc

    if len(raw) > max_download_bytes:
        raise TelegramError(
            f"The text file is larger than {max_download_bytes:,} bytes."
        )

    return raw.decode("utf-8-sig", errors="replace")
