from __future__ import annotations


def split_text(text: str, max_chars: int = 1200, overlap_chars: int = 150) -> list[str]:
    normalized = " ".join(text.replace("\r", "\n").split())
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    chunks: list[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + max_chars, length)

        # 优先按句号/问号等断句，减少语义被强制切断。
        if end < length:
            pivot = max(
                normalized.rfind("。", start, end),
                normalized.rfind("！", start, end),
                normalized.rfind("？", start, end),
                normalized.rfind(".", start, end),
            )
            if pivot > start + int(max_chars * 0.6):
                end = pivot + 1

        chunks.append(normalized[start:end].strip())
        if end >= length:
            break

        start = max(0, end - overlap_chars)

    return [chunk for chunk in chunks if chunk]

