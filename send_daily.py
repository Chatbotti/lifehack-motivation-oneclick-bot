#!/usr/bin/env python3
"""Send one manually curated Lifehack Motivation link to Telegram."""

from __future__ import annotations

import html
import json
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from telegram_api import send_message

ARTICLES_FILE = Path(__file__).with_name("articles.json")
DEFAULT_START_DATE = "2026-07-13"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is empty. Add it under GitHub repository "
            "Settings > Secrets and variables > Actions."
        )
    return value


def load_chat_ids() -> list[str]:
    """Read one or more comma-separated Telegram chat IDs."""
    raw = require_env("TELEGRAM_CHAT_ID")
    chat_ids: list[str] = []

    for item in raw.split(","):
        chat_id = item.strip()
        if chat_id and chat_id not in chat_ids:
            chat_ids.append(chat_id)

    if not chat_ids:
        raise RuntimeError("TELEGRAM_CHAT_ID contains no usable chat IDs.")

    return chat_ids


def load_articles() -> list[dict[str, str]]:
    data = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise RuntimeError("articles.json must contain at least one entry.")

    cleaned: list[dict[str, str]] = []
    for number, item in enumerate(data, start=1):
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        if not title or not url.startswith(("https://lifehack.org/", "https://www.lifehack.org/")):
            raise RuntimeError(f"Invalid Lifehack article at position {number}.")
        cleaned.append({"title": title, "url": url})
    return cleaned


def _daily_index(articles: list[dict[str, str]], day: date) -> int:
    """Return a reproducible random-looking index for a calendar day."""
    rng = random.Random(f"lifehack-motivation:{day.isoformat()}")
    return rng.randrange(len(articles))


def choose_article(articles: list[dict[str, str]]) -> tuple[int, dict[str, str]]:
    """Choose a daily random article and avoid yesterday's article if possible."""
    today = date.today()
    index = _daily_index(articles, today)

    if len(articles) > 1:
        yesterday_index = _daily_index(articles, today - timedelta(days=1))
        if index == yesterday_index:
            index = (index + 1) % len(articles)

    return index, articles[index]


def main() -> int:
    try:
        token = require_env("TELEGRAM_BOT_TOKEN")
        chat_ids = load_chat_ids()
        articles = load_articles()
        index, article = choose_article(articles)

        message = (
            "📚 Daily Motivation Reading\n\n"
            f"Article {index + 1} of {len(articles)}\n"
            f"{article['title']}\n"
            f"{article['url']}\n\n"
            "1. Open and read the article normally.\n"
            "2. Copy the text for your personal study.\n"
            "3. Paste it into this bot or upload a UTF-8 .txt file.\n"
            "4. The bot will return TTS parts of at most 3,000 bytes.\n"
            "5. Summarize the article in your own words and speak for 2 minutes."
        )
        for chat_id in chat_ids:
            send_message(token, chat_id, message)

        print(
            f"Sent article #{index + 1} to {len(chat_ids)} chat(s): "
            f"{article['title']}"
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
