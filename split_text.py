"""Sentence-aware UTF-8 byte chunking for text-to-speech inputs."""

from __future__ import annotations

import re
import unicodedata

DEFAULT_MAX_BYTES = 3000


def utf8_size(text: str) -> int:
    """Return the number of bytes used by text when encoded as UTF-8."""
    return len(text.encode("utf-8"))


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace while retaining useful paragraphs."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines: list[str] = []
    previous_blank = False

    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        is_blank = not line

        if is_blank:
            if cleaned_lines and not previous_blank:
                cleaned_lines.append("")
        else:
            cleaned_lines.append(line)

        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


def _hard_split_utf8(text: str, max_bytes: int) -> list[str]:
    """Split text by Unicode code point without breaking a UTF-8 sequence."""
    chunks: list[str] = []
    current: list[str] = []
    current_bytes = 0

    for char in text:
        char_bytes = utf8_size(char)
        if char_bytes > max_bytes:
            raise ValueError("max_bytes is too small for one Unicode character")

        if current and current_bytes + char_bytes > max_bytes:
            chunks.append("".join(current))
            current = [char]
            current_bytes = char_bytes
        else:
            current.append(char)
            current_bytes += char_bytes

    if current:
        chunks.append("".join(current))

    return chunks


def _split_oversized_unit(unit: str, max_bytes: int) -> list[str]:
    """Prefer word boundaries; hard-split only a single oversized token."""
    words = unit.split()
    if not words:
        return []

    chunks: list[str] = []
    current = ""

    for word in words:
        if utf8_size(word) > max_bytes:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split_utf8(word, max_bytes))
            continue

        candidate = word if not current else f"{current} {word}"
        if utf8_size(candidate) <= max_bytes:
            current = candidate
        else:
            chunks.append(current)
            current = word

    if current:
        chunks.append(current)

    return chunks


def _sentence_units(text: str) -> list[str]:
    """Turn paragraphs into sentence-like units suitable for TTS."""
    units: list[str] = []

    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        sentences = re.split(r"(?<=[.!?…])(?:[\"'”’)\]]*)\s+", paragraph)
        units.extend(sentence.strip() for sentence in sentences if sentence.strip())

    return units


def split_for_tts(text: str, max_bytes: int = DEFAULT_MAX_BYTES) -> list[str]:
    """Split text into natural chunks, each no larger than max_bytes in UTF-8.

    The function prefers sentence boundaries, then word boundaries, and finally
    Unicode code-point boundaries. It never cuts through a UTF-8 byte sequence.
    """
    if max_bytes < 4:
        raise ValueError("max_bytes must be at least 4")

    normalized = normalize_text(text)
    if not normalized:
        return []

    prepared_units: list[str] = []
    for unit in _sentence_units(normalized):
        if utf8_size(unit) <= max_bytes:
            prepared_units.append(unit)
        else:
            prepared_units.extend(_split_oversized_unit(unit, max_bytes))

    chunks: list[str] = []
    current = ""

    for unit in prepared_units:
        candidate = unit if not current else f"{current} {unit}"
        if utf8_size(candidate) <= max_bytes:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = unit

    if current:
        chunks.append(current)

    assert all(0 < utf8_size(chunk) <= max_bytes for chunk in chunks)
    return chunks
