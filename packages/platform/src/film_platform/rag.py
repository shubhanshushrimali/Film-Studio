"""Cut a script into scene chunks. Embeddings are a later plug-in."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING = re.compile(
    r"(?im)^\s*(?:INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.).+$"
)


@dataclass(frozen=True)
class Chunk:
    index: int
    heading: str
    text: str
    start: int


def chunk_scenes(script: str, *, max_chars: int = 4000) -> list[Chunk]:
    """One chunk per scene heading. Long scenes split, with the heading repeated."""
    text = script.replace("\r\n", "\n").strip()
    if not text:
        return []
    marks = list(_HEADING.finditer(text))
    if not marks:
        return _split(0, "UNTITLED", text, 0, max_chars)
    chunks: list[Chunk] = []
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        body = text[mark.start() : end].strip()
        heading = mark.group(0).strip()
        chunks.extend(_split(len(chunks), heading, body, mark.start(), max_chars))
    return chunks


def _split(start_index: int, heading: str, body: str, start: int, max_chars: int) -> list[Chunk]:
    if len(body) <= max_chars:
        return [Chunk(start_index, heading, body, start)]
    parts: list[Chunk] = []
    cursor = 0
    while cursor < len(body):
        piece = body[cursor : cursor + max_chars].strip()
        if piece:
            parts.append(Chunk(start_index + len(parts), heading, piece, start + cursor))
        cursor += max_chars
    return parts
