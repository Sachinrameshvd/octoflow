"""Attachment extraction for images, PDFs, and text files in OctoFlow chat.

Supports drag-and-drop paths, @filepath mentions, quoted paths, and relative paths.
"""

from __future__ import annotations

import base64
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTS: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

TEXT_EXTS: set[str] = {
    ".txt",
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".log",
    ".html",
    ".css",
    ".sh",
    ".sql",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
}

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB
MAX_TEXT_CHARS = 24_000


@dataclass
class ImageAttachment:
    """Base64-encoded image attachment ready for multimodal LLM providers."""

    path: str
    filename: str
    media_type: str
    base64_data: str


def _resolve_candidate_path(raw: str, workspace: Path | None = None) -> Path | None:
    """Resolve a raw token or dragged path to an existing file on disk."""
    cleaned = raw.strip().strip("\"'")
    if cleaned.startswith("@"):
        cleaned = cleaned[1:].strip().strip("\"'")
    # Unescape macOS Terminal drag-and-drop backslashes (e.g. Octoflow\ copy)
    unescaped = cleaned.replace("\\ ", " ")
    for candidate_str in (unescaped, cleaned):
        if not candidate_str:
            continue
        p = Path(candidate_str).expanduser()
        if not p.is_absolute() and workspace is not None:
            ws_p = (workspace / p).resolve()
            if ws_p.is_file():
                return ws_p
        if p.is_file():
            return p.resolve()
    return None


def _extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using pypdf if available, else pdftotext/strings fallback."""
    try:
        import pypdf  # type: ignore[import-not-found]

        reader = pypdf.PdfReader(str(pdf_path))
        pages: list[str] = []
        for idx, page in enumerate(reader.pages, start=1):
            txt = (page.extract_text() or "").strip()
            if txt:
                pages.append(f"--- Page {idx} ---\n{txt}")
        if pages:
            return "\n\n".join(pages)[:MAX_TEXT_CHARS]
    except Exception:
        pass

    # Fallback 1: pdftotext CLI (common on macOS/Linux via poppler)
    try:
        res = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()[:MAX_TEXT_CHARS]
    except Exception:
        pass

    # Fallback 2: macOS mdls / spotlight text or raw printable ASCII extraction
    try:
        raw_bytes = pdf_path.read_bytes()
        text_chunks = re.findall(rb"\(([^()]{3,200})\)", raw_bytes)
        decoded = " ".join(c.decode("latin-1", errors="ignore") for c in text_chunks)
        if len(decoded.strip()) > 30:
            return decoded.strip()[:MAX_TEXT_CHARS]
    except Exception:
        pass

    return "[PDF detected, but text extraction requires 'pypdf' (pip install pypdf) or 'pdftotext'.]"


def _find_path_candidates(message: str) -> list[str]:
    """Extract quoted, @-prefixed, escaped-space, or bare path tokens from user text."""
    candidates: list[str] = []
    seen: set[str] = set()

    patterns = [
        r'@?"([^"]+)"',
        r"@?'([^']+)'",
        r"@((?:~|/|(?:\.\.?/))?(?:[^\s\\]|\\ )+)",
        r"((?:~|/)(?:[^\s\\]|\\ )+)",
    ]
    for pat in patterns:
        for m in re.finditer(pat, message):
            val = m.group(1)
            if val not in seen:
                seen.add(val)
                candidates.append(val)

    # Also check whitespace-separated tokens for relative filenames (e.g. README.md, shot.png)
    for tok in message.split():
        stripped = tok.strip(".,;:!?()[]\"'")
        if stripped.startswith("@"):
            stripped = stripped[1:]
        if "." in stripped and stripped not in seen:
            seen.add(stripped)
            candidates.append(stripped)

    return candidates


def extract_attachments_from_message(
    message: str, workspace: Path | None = None
) -> tuple[str, list[ImageAttachment], str, list[str]]:
    """Parse images, PDFs, and text files from a chat message.

    Returns:
        (prompt_text, image_attachments, text_context, badge_descriptions)
    """
    images: list[ImageAttachment] = []
    text_blocks: list[str] = []
    badges: list[str] = []
    seen_resolved: set[Path] = set()

    for raw in _find_path_candidates(message):
        resolved = _resolve_candidate_path(raw, workspace=workspace)
        if resolved is None or resolved in seen_resolved:
            continue
        seen_resolved.add(resolved)

        ext = resolved.suffix.lower()
        if ext in IMAGE_EXTS:
            try:
                size = resolved.stat().st_size
                if size > MAX_IMAGE_BYTES:
                    badges.append(f"{resolved.name} (skipped: >15MB)")
                    continue
                b64 = base64.b64encode(resolved.read_bytes()).decode("ascii")
                images.append(
                    ImageAttachment(
                        path=str(resolved),
                        filename=resolved.name,
                        media_type=IMAGE_EXTS[ext],
                        base64_data=b64,
                    )
                )
                kb = max(1, size // 1024)
                badges.append(f"{resolved.name} (image, {kb} KB)")
            except Exception:
                continue
        elif ext == ".pdf":
            extracted = _extract_pdf_text(resolved)
            text_blocks.append(f"Attached PDF [{resolved.name}]:\n{extracted}")
            badges.append(f"{resolved.name} (pdf)")
        elif ext in TEXT_EXTS:
            try:
                content = resolved.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_CHARS]
                text_blocks.append(f"Attached File [{resolved.name}]:\n{content}")
                badges.append(f"{resolved.name} (text)")
            except Exception:
                continue

    text_context = "\n\n".join(text_blocks)
    return message, images, text_context, badges

