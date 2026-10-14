#!/usr/bin/env python3
"""Extract plain text from job-description files.

Supported inputs: .docx, .pages, .pdf, .txt, .md, .html

The .docx and .pages routes deliberately use only the standard library (zipfile +
re), so the script works in a bare environment. .pdf needs pypdf, and .html needs
nothing beyond html.parser.

Usage:
    python extract_text.py JD.docx --out ./jds/
    python extract_text.py ./jds/ --out ./jds_txt/     # batch a directory
    python extract_text.py JD.pdf                       # print to stdout
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

CJK_RUN = re.compile(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"
                     r"A-Za-z0-9@._%+:/()\-—、，。：；·｜| ]{2,}")


# --------------------------------------------------------------------------- #
# .docx
# --------------------------------------------------------------------------- #
def extract_docx(path: Path) -> str:
    """Pull w:t text runs out of word/document.xml in document order."""
    with zipfile.ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            raise ValueError(f"{path} is not a DOCX (no word/document.xml)")
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")

    # Split into paragraphs FIRST, then pull the text runs inside each one, so the
    # paragraph boundary survives as a newline. (Replacing `</w:p>` with "\n" on the
    # whole document does nothing useful: that newline sits *between* w:t elements
    # and is discarded by the text-run extraction.)
    #
    # NOTE the `(?:\s[^>]*)?` tag boundary: without it, `<w:t[^>]*>` also matches
    # `</w:tabs>` and leaks raw XML into the output.
    paragraphs: list[str] = []
    for para in re.findall(r"<w:p(?:\s[^>]*)?>(.*?)</w:p>", xml, re.S):
        para = re.sub(r"<w:tab(?:\s[^>]*)?/>", " ", para)
        para = re.sub(r"<w:br(?:\s[^>]*)?/>", "\n", para)
        runs = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", para, re.S)
        paragraphs.append("".join(runs))

    # Fall back to a whole-document sweep for shapes/textboxes outside w:p
    if not paragraphs:
        paragraphs = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", xml, re.S)

    text = "\n".join(paragraphs)
    text = _unescape_xml(text)
    return _tidy(text)


# --------------------------------------------------------------------------- #
# .pages  (Apple Pages = zip; body text lives in Index/Document.iwa)
# --------------------------------------------------------------------------- #
def extract_pages(path: Path) -> str:
    """Best-effort text recovery from an Apple Pages document.

    Index/Document.iwa is a protobuf stream, not plain text. Decoding the bytes as
    UTF-8 and collecting character runs recovers most long passages, but short
    fragments can be lost where the text is split across message boundaries.
    Treat the result as LOSSY and verify anything you intend to quote.
    """
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if not any(n.startswith("Index/") for n in names):
            raise ValueError(f"{path} is not a Pages document")
        blobs = [z.read(n) for n in names if n.endswith(".iwa")]

    out: list[str] = []
    seen: set[str] = set()
    for blob in blobs:
        decoded = blob.decode("utf-8", errors="ignore")
        for m in CJK_RUN.finditer(decoded):
            run = m.group(0).strip()
            # Require real CJK content: the raw decode also surfaces locale tags,
            # calendar names and numbers that are not job-description text.
            cjk = sum(1 for ch in run if "\u4e00" <= ch <= "\u9fff")
            if cjk >= 2 and len(run) > 2 and run not in seen:
                seen.add(run)
                out.append(run)
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# .pdf
# --------------------------------------------------------------------------- #
def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        raise SystemExit(
            "PDF support needs pypdf. Install it with:  pip install pypdf"
        )
    reader = PdfReader(str(path))
    return _tidy("\n".join((page.extract_text() or "") for page in reader.pages))


# --------------------------------------------------------------------------- #
# .html
# --------------------------------------------------------------------------- #
class _TextFromHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._skip += 1
        elif tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def extract_html(path: Path) -> str:
    parser = _TextFromHTML()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return _tidy("".join(parser.parts))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _unescape_xml(text: str) -> str:
    return (
        text.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&amp;", "&")
    )


def _tidy(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


EXTRACTORS = {
    ".docx": extract_docx,
    ".pages": extract_pages,
    ".pdf": extract_pdf,
    ".html": extract_html,
    ".htm": extract_html,
    ".txt": lambda p: _tidy(p.read_text(encoding="utf-8", errors="ignore")),
    ".md": lambda p: _tidy(p.read_text(encoding="utf-8", errors="ignore")),
}


def extract_one(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in EXTRACTORS:
        raise ValueError(f"unsupported type: {suffix} ({path.name})")
    return EXTRACTORS[suffix](path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="a file, or a directory to batch")
    ap.add_argument("--out", help="output directory; omit to print to stdout")
    args = ap.parse_args()

    src = Path(args.input)
    targets: list[Path]
    if src.is_dir():
        targets = sorted(
            p for p in src.rglob("*")
            if p.is_file() and p.suffix.lower() in EXTRACTORS
        )
    else:
        targets = [src]

    if not targets:
        print("no supported files found", file=sys.stderr)
        return 1

    outdir = Path(args.out) if args.out else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for path in targets:
        try:
            text = extract_one(path)
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"[FAIL] {path.name}: {exc}", file=sys.stderr)
            failures += 1
            continue

        if outdir:
            dest = outdir / (path.stem + ".txt")
            dest.write_text(text, encoding="utf-8")
            print(f"[ok] {path.name} -> {dest} ({len(text)} chars)")
        else:
            if len(targets) > 1:
                print(f"\n===== {path.name} =====\n")
            print(text)

        if path.suffix.lower() == ".pages":
            print("     note: .pages extraction is lossy - verify quoted text",
                  file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
