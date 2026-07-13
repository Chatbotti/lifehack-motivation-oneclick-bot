"""Telegram webhook that splits user-provided text into TTS-safe chunks."""

from __future__ import annotations

import hmac
import os
import re
import time
from typing import Any

from flask import Flask, abort, jsonify, request

from split_text import DEFAULT_MAX_BYTES, split_for_tts, utf8_size
from telegram_api import TelegramError, download_text_document, send_message

app = Flask(__name__)

HELP_TEXT = """Send me text and I will divide it into natural TTS parts.

Options:
• Paste text directly.
• Upload a UTF-8 .txt or .md file.
• Use /split followed by text.

Every returned text part is at most 3,000 UTF-8 bytes.
For a Lifehack article, you can also open it in Chrome/Edge and click the supplied browser-extension icon. The extension extracts the visible article locally and sends only the cleaned text to this private bot.
"""


def env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is missing.")
    return value


def is_owner(chat_id: str) -> bool:
    owner_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    return bool(owner_chat_id) and hmac.compare_digest(chat_id, owner_chat_id)


def looks_like_url_only(text: str) -> bool:
    return bool(re.fullmatch(r"https?://\S+", text.strip(), flags=re.IGNORECASE))


def process_text(token: str, chat_id: str, text: str) -> None:
    chunks = split_for_tts(text, DEFAULT_MAX_BYTES)
    if not chunks:
        send_message(token, chat_id, "I could not find any readable text.")
        return

    send_message(
        token,
        chat_id,
        (
            f"Prepared {len(chunks)} TTS part(s). "
            f"Each following text message is ≤ {DEFAULT_MAX_BYTES:,} UTF-8 bytes."
        ),
    )

    for index, chunk in enumerate(chunks, start=1):
        send_message(
            token,
            chat_id,
            f"Part {index}/{len(chunks)} · {utf8_size(chunk):,} bytes",
        )
        send_message(token, chat_id, chunk)
        time.sleep(0.08)


def handle_message(message: dict[str, Any]) -> None:
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not chat_id or not is_owner(chat_id):
        return

    text = str(message.get("text", "")).strip()

    if text.startswith("/start") or text.startswith("/help"):
        send_message(token, chat_id, HELP_TEXT)
        return

    if text.startswith("/limit"):
        send_message(
            token,
            chat_id,
            (
                f"The configured TTS limit is {DEFAULT_MAX_BYTES:,} UTF-8 bytes. "
                "English letters usually use 1 byte; many non-Latin characters "
                "use more than 1 byte."
            ),
        )
        return

    document = message.get("document")
    if isinstance(document, dict):
        filename = str(document.get("file_name", "")).lower()
        mime_type = str(document.get("mime_type", "")).lower()
        file_size = int(document.get("file_size", 0) or 0)

        accepted = (
            filename.endswith((".txt", ".md"))
            or mime_type in {"text/plain", "text/markdown"}
        )
        if not accepted:
            send_message(token, chat_id, "Please upload a .txt or .md text file.")
            return

        if file_size and file_size > 250_000:
            send_message(token, chat_id, "The text file must be 250 KB or smaller.")
            return

        try:
            contents = download_text_document(token, str(document["file_id"]))
            process_text(token, chat_id, contents)
        except (KeyError, TelegramError, ValueError) as exc:
            send_message(token, chat_id, f"I could not process that file: {exc}")
        return

    if text.startswith("/split"):
        text = text[len("/split"):].strip()
        if not text:
            send_message(
                token,
                chat_id,
                "Put text after /split, paste it as a normal message, or upload a .txt file.",
            )
            return

    elif text.startswith("/"):
        send_message(token, chat_id, HELP_TEXT)
        return

    if not text:
        send_message(token, chat_id, "Please send text or upload a .txt file.")
        return

    if looks_like_url_only(text):
        send_message(
            token,
            chat_id,
            (
                "I do not automatically extract Lifehack pages. Open the article "
                "normally, copy its text for your personal study, and paste it here "
                "or upload it as a UTF-8 .txt file."
            ),
        )
        return

    try:
        process_text(token, chat_id, text)
    except (TelegramError, ValueError) as exc:
        send_message(token, chat_id, f"I could not split that text: {exc}")


@app.post("/submit")
def submit_from_browser():
    """Accept article text extracted locally by the user's browser extension."""
    expected = env("SUBMIT_SECRET")
    supplied = request.headers.get("Authorization", "")
    expected_header = f"Bearer {expected}"

    if not hmac.compare_digest(supplied, expected_header):
        abort(403)

    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    source_url = str(payload.get("url", "")).strip()
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify(ok=False, error="No article text was supplied."), 400

    if len(text.encode("utf-8")) > 250_000:
        return jsonify(ok=False, error="Article text exceeds the 250 KB limit."), 413

    if source_url:
        match = re.fullmatch(
            r"https://(?:www\.)?lifehack\.org(?:/.*)?",
            source_url,
            flags=re.IGNORECASE,
        )
        if not match:
            return jsonify(ok=False, error="Only Lifehack article pages are accepted."), 400

    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")

    if title:
        send_message(token, chat_id, f"📖 Extracted article\n{title}\n{source_url}".strip())

    process_text(token, chat_id, text)

    return jsonify(
        ok=True,
        bytes=len(text.encode("utf-8")),
        title=title,
    )


@app.get("/")
@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return {"status": "ok"}, 200


@app.post("/telegram/<path_secret>")
def telegram_webhook(path_secret: str):
    expected = env("WEBHOOK_SECRET")
    supplied_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    if not hmac.compare_digest(path_secret, expected):
        abort(404)
    if not hmac.compare_digest(supplied_header, expected):
        abort(403)

    update = request.get_json(silent=True) or {}
    message = update.get("message")

    if isinstance(message, dict):
        handle_message(message)

    return jsonify(ok=True)


@app.errorhandler(Exception)
def unexpected_error(exc: Exception):
    app.logger.exception("Unhandled error: %s", exc)
    return jsonify(ok=False), 500
