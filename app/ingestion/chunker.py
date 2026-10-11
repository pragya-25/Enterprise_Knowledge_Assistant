"""Turn one Markdown page into small, self-contained chunks with metadata."""
import re
from app.core.config import MAX_CHUNK_CHARS, OVERLAP_CHARS, MIN_CHUNK_CHARS

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SHORTCODE = re.compile(r"\{\{[%<].*?[%>]\}\}", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


def parse_front_matter(text: str):
    """Return (title, body). Handbook pages start with a YAML-like header."""
    title = None
    m = FRONT_MATTER.match(text)
    if m:
        for line in m.group(1).splitlines():
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip().strip("\"'")
        text = text[m.end():]
    return title, text


def clean(text: str) -> str:
    text = HTML_COMMENT.sub("", text)
    text = SHORTCODE.sub("", text)
    text = IMAGE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def split_long(text: str):
    """Split an oversized section on paragraph boundaries, with a small overlap."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", text):
        if current and len(current) + len(para) + 2 > MAX_CHUNK_CHARS:
            parts.append(current.strip())
            current = current[-OVERLAP_CHARS:] + "\n\n" + para
        else:
            current = f"{current}\n\n{para}" if current else para
        # a single giant paragraph: hard split
        while len(current) > MAX_CHUNK_CHARS:
            parts.append(current[:MAX_CHUNK_CHARS].strip())
            current = current[MAX_CHUNK_CHARS - OVERLAP_CHARS:]
    if current.strip():
        parts.append(current.strip())
    return parts


def chunk_markdown(raw_text: str, fallback_title: str):
    title, body = parse_front_matter(raw_text)
    title = title or fallback_title
    body = clean(body)

    # 1. split into sections by heading, remembering the heading path
    sections, path, buf = [], [], []

    def flush():
        text = "\n".join(buf).strip()
        if text:
            sections.append((" > ".join(path), text))
        buf.clear()

    for line in body.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            path[:] = path[: level - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    flush()

    # 2. split long sections, drop tiny ones
    chunks = []
    for section, text in sections:
        for piece in split_long(text):
            if len(piece) >= MIN_CHUNK_CHARS:
                chunks.append({"title": title, "section": section or title, "text": piece})
    return chunks
