from __future__ import annotations

import re

from .models import Chunk


ARTICLE_RE = re.compile(
    r"(?im)^[ \t]*(?P<label>(?:GEÇİCİ\s+|EK\s+|MÜKERRER\s+)?MADDE\s+"
    r"[0-9]+(?:\s*/\s*[0-9A-ZÇĞİÖŞÜ]+)?)\s*[-–—:.]?\s*"
)
HEADING_RE = re.compile(
    r"(?m)^[ \t]*(?P<heading>(?:BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ|ALTINCI|YEDİNCİ|"
    r"SEKİZİNCİ|DOKUZUNCU|ONUNCU)\s+(?:BÖLÜM|KISIM)|[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s]{5,})\s*$"
)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    parts: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            parts.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        parts.append(current)

    bounded: list[str] = []
    for part in parts:
        start = 0
        while len(part) - start > max_chars:
            ceiling = start + max_chars
            floor = start + max_chars // 2
            cut = max(
                part.rfind("\n", floor, ceiling),
                part.rfind(". ", floor, ceiling),
                part.rfind("; ", floor, ceiling),
                part.rfind(" ", floor, ceiling),
            )
            if cut < floor:
                cut = ceiling
            elif part[cut : cut + 2] in {". ", "; "}:
                cut += 1
            bounded.append(part[start:cut].strip())
            start = max(start + 1, cut - overlap)
        tail = part[start:].strip()
        if tail:
            bounded.append(tail)
    return bounded


def chunk_legal_text(
    text: str, max_chars: int = 5500, overlap: int = 350
) -> list[Chunk]:
    text = normalize_text(text)
    article_matches = list(ARTICLE_RE.finditer(text))
    heading_matches = list(HEADING_RE.finditer(text))
    raw_sections: list[tuple[str | None, str]] = []

    markers: list[tuple[int, str]] = []
    markers.extend((match.start(), match.group("label").strip()) for match in article_matches)
    markers.extend((match.start(), match.group("heading").strip()) for match in heading_matches)
    markers = sorted(dict(markers).items())

    if markers:
        preamble = text[: markers[0][0]].strip()
        if preamble:
            raw_sections.append((None, preamble))
        for idx, (start, label) in enumerate(markers):
            end = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
            raw_sections.append((label, text[start:end].strip()))
    else:
        raw_sections.append((None, text))

    chunks: list[Chunk] = []
    ordinal = 0
    for label, section in raw_sections:
        for part_index, part in enumerate(_split_long(section, max_chars, overlap)):
            article_no = None
            heading = label
            if label and "MADDE" in label.upper():
                article_no = re.sub(r"(?i)^.*?MADDE\s+", "", label).strip()
            chunks.append(
                Chunk(
                    ordinal=ordinal,
                    text=part,
                    heading=heading,
                    article_no=article_no,
                    metadata={"part_index": part_index},
                )
            )
            ordinal += 1
    return chunks
