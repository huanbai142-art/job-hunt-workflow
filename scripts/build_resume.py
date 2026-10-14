#!/usr/bin/env python3
"""Build a resume .docx from a YAML/JSON config.

Two layout profiles are supported:

  modern : photo top-right, thin underlined section heads, right-aligned dates,
           bold keyword line. Common for mainland-China campus recruiting.
  ats    : photo-free, single column, centered header, dark-blue section heads.

The generator encodes the OOXML traps documented in
references/03-resume-formatting.md:

  * pPr children are emitted in schema order (pBdr < tabs < spacing < ind < jc),
    otherwise Word refuses to open the file;
  * w:eastAsia is set explicitly, or CJK glyphs fall back to the theme font;
  * oversized runs get a taller line box so exact line spacing cannot clip them.

Usage:
    pip install python-docx pyyaml
    python build_resume.py config.yaml --out ./out/
    python build_resume.py config.yaml --out ./out/ --verify
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml import parse_xml
    from docx.oxml.ns import qn
    from docx.shared import Cm, Emu, Pt, RGBColor
except ImportError:
    raise SystemExit("This script needs python-docx:  pip install python-docx")

try:
    import yaml
except ImportError:
    raise SystemExit("This script needs PyYAML:  pip install pyyaml")

EMU_PER_TWIP = 635
A4_W_TWIP, A4_H_TWIP = 11906, 16838


# --------------------------------------------------------------------------- #
# low-level helpers
# --------------------------------------------------------------------------- #
def set_font(run, *, ea: str, latin: str, size: float,
             color: str | None = None, bold: bool = False) -> None:
    """Set run font including the East-Asian attribute and optional colour."""
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), ea)
    rFonts.set(qn("w:ascii"), latin)
    rFonts.set(qn("w:hAnsi"), latin)
    rFonts.set(qn("w:cs"), latin)


def _space(p, before: float, after: float, line: float | None) -> None:
    pf = p.paragraph_format
    if line is not None:
        pf.line_spacing = Pt(line)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)


def add_section_head(doc, text, spec):
    """Section head with a hairline bottom rule.

    w:pBdr MUST be inserted before w:spacing to satisfy the CT_PPr sequence.
    """
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _space(p, 0, 0, spec["line"])
    pPr = p._p.get_or_add_pPr()
    pBdr = pPr.makeelement(qn("w:pBdr"), {})
    bottom = pBdr.makeelement(qn("w:bottom"), {})
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(spec["rule_sz"]))      # eighths of a point
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), spec["accent"].lstrip("#"))
    pBdr.append(bottom)
    pPr.insert(0, pBdr)                                # BEFORE spacing / jc
    run = p.add_run(text)
    set_font(run, ea=spec["ea"], latin=spec["latin"],
             size=spec["head_size"], color=spec["accent"], bold=True)
    return p


def add_entry(doc, title, date, spec):
    """Entry title with a right-aligned date on the same line."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _space(p, 0, 0, spec["line"])
    pf.tab_stops.add_tab_stop(Cm(spec["text_width_cm"]), 2)  # 2 = RIGHT tab
    r1 = p.add_run(title)
    set_font(r1, ea=spec["ea"], latin=spec["latin"],
             size=spec["entry_size"], color=spec["text"], bold=True)
    if date:
        r2 = p.add_run("\t" + date)
        set_font(r2, ea=spec["latin"], latin=spec["latin"],
                 size=spec["date_size"], color=spec["date_color"], bold=False)
    return p


def add_body(doc, text, spec, *, bullet: bool = False):
    """A body paragraph; optionally a hanging-indent bullet.

    For a bullet, w:spacing is written before w:ind, per the schema order.
    """
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = (WD_ALIGN_PARAGRAPH.JUSTIFY if spec["justify"]
                    else WD_ALIGN_PARAGRAPH.LEFT)
    _space(p, 0, 0, spec["line"])       # w:spacing first
    if bullet:
        pf.left_indent = Cm(0.5)        # w:ind second
        pf.first_line_indent = Cm(-0.5)
        text = spec["bullet"] + text
    run = p.add_run(text)
    set_font(run, ea=spec["ea"], latin=spec["latin"],
             size=spec["body_size"], color=spec["text"], bold=False)
    return p


def add_kv(doc, label, value, spec):
    """Bold label + regular value on one line (used by the skills block)."""
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _space(p, 0, 0, spec["line"])
    r1 = p.add_run(label + "：")
    set_font(r1, ea=spec["ea"], latin=spec["latin"],
             size=spec["body_size"], color=spec["text"], bold=True)
    r2 = p.add_run(value)
    set_font(r2, ea=spec["ea"], latin=spec["latin"],
             size=spec["body_size"], color=spec["text"], bold=False)
    return p


def attach_floating_photo(doc, paragraph, image_path: str,
                          width_emu: int = 936625, height_emu: int = 1368425,
                          x_emu: int = 5029200, y_emu: int = 34290) -> None:
    """Anchor a photo to the top-right of `paragraph` with no text wrapping."""
    rid, _ = doc.part.get_or_add_image(image_path)
    anchor = (
        '<wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'distT="0" distB="0" distL="114300" distR="114300" simplePos="0" '
        'relativeHeight="251659264" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="column"><wp:posOffset>{x_emu}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="paragraph"><wp:posOffset>{y_emu}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        '<wp:effectExtent l="0" t="0" r="3175" b="3175"/><wp:wrapNone/>'
        '<wp:docPr id="1" name="Picture 1"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="photo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{int(width_emu * 0.99933)}" cy="{int(height_emu * 0.99933)}"/></a:xfrm>'
        '<a:prstGeom prst="rect"/></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:anchor>'
    )
    drawing = ('<w:drawing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               + anchor + "</w:drawing>")
    run = paragraph.add_run()
    run._r.append(parse_xml(drawing))


# --------------------------------------------------------------------------- #
# style specs
# --------------------------------------------------------------------------- #
def style_spec(profile: str) -> dict:
    if profile == "modern":
        return dict(
            ea="宋体", latin="Arial", accent="1A1A1A", text="1A1A1A",
            muted="888888", date_color="888888", keyword_color="444444",
            line=264 / 20, body_size=10.5, head_size=10, entry_size=11,
            date_size=10, name_size=20, meta_size=9.5, rule_sz=2,
            text_width_cm=18.0, justify=False, bullet="-  ",
            name_align="left", header_align="left",
        )
    # ats (default)
    return dict(
        ea="微软雅黑", latin="Microsoft YaHei", accent="1F4E79", text="000000",
        muted="000000", date_color="404040", keyword_color="000000",
        line=14.5, body_size=9, head_size=10.5, entry_size=9.5,
        date_size=9, name_size=18, meta_size=9, rule_sz=4,
        text_width_cm=18.0, justify=True, bullet="•\u2002",
        name_align="center", header_align="center",
    )


# --------------------------------------------------------------------------- #
# builder
# --------------------------------------------------------------------------- #
def build(cfg: dict, out_dir: Path) -> Path:
    profile = cfg.get("style", "ats")
    spec = style_spec(profile)
    doc = Document()

    sec = doc.sections[0]
    m = cfg.get("page", {})
    sec.page_width = Emu(A4_W_TWIP * EMU_PER_TWIP)
    sec.page_height = Emu(A4_H_TWIP * EMU_PER_TWIP)
    sec.top_margin = Cm(m.get("top_cm", 1.3))
    sec.bottom_margin = Cm(m.get("bottom_cm", 1.3))
    sec.left_margin = Cm(m.get("left_cm", 1.5))
    sec.right_margin = Cm(m.get("right_cm", 1.5))
    sec.header_distance = Cm(m.get("header_cm", 0.5))
    sec.footer_distance = Cm(m.get("footer_cm", 0.5))

    # --- header block ------------------------------------------------------ #
    h = cfg["header"]
    align = (WD_ALIGN_PARAGRAPH.CENTER if spec["name_align"] == "center"
             else WD_ALIGN_PARAGRAPH.LEFT)

    name_p = doc.add_paragraph()
    name_p.paragraph_format.alignment = align
    # the 18pt name needs a taller box than the body's exact line height
    _space(name_p, 0, 2, None)
    name_p.paragraph_format.line_spacing = Pt(spec["name_size"] * 1.34)
    name_p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY

    photo = h.get("photo")
    if profile == "modern" and photo and Path(photo).exists():
        r = name_p.add_run(h["name"])
        set_font(r, ea=spec["ea"], latin=spec["latin"],
                 size=spec["name_size"], color=spec["text"], bold=True)
        attach_floating_photo(doc, name_p, photo)
    else:
        r = name_p.add_run(h["name"])
        set_font(r, ea=spec["ea"], latin=spec["latin"],
                 size=spec["name_size"], color=spec["text"], bold=True)

    for line in h.get("meta_lines", []):
        p = doc.add_paragraph()
        p.paragraph_format.alignment = align
        _space(p, 0, 0, spec["line"])
        r = p.add_run(line)
        set_font(r, ea=spec["ea"], latin=spec["latin"],
                 size=spec["meta_size"], color=spec["muted"], bold=False)

    if h.get("keywords"):
        p = doc.add_paragraph()
        p.paragraph_format.alignment = align
        _space(p, 0, 0, spec["line"])
        r = p.add_run(h["keywords"])
        set_font(r, ea=spec["ea"], latin=spec["latin"],
                 size=spec["meta_size"], color=spec["keyword_color"], bold=False)

    if h.get("target"):
        p = doc.add_paragraph()
        p.paragraph_format.alignment = align
        _space(p, 0, 4, spec["line"])
        r = p.add_run(h["target"])
        set_font(r, ea=spec["ea"], latin=spec["latin"],
                 size=spec["meta_size"] + 1, color=spec["text"], bold=True)

    # --- sections ---------------------------------------------------------- #
    for s in cfg.get("sections", []):
        add_section_head(doc, s["title"], spec)

        if s.get("paragraph"):
            add_body(doc, s["paragraph"], spec)

        for entry in s.get("entries", []):
            add_entry(doc, entry["title"], entry.get("date", ""), spec)
            if entry.get("subtitle"):
                add_body(doc, entry["subtitle"], spec)
            for b in entry.get("bullets", []):
                add_body(doc, b, spec, bullet=True)

        for label, value in s.get("kv", []):
            add_kv(doc, label, value, spec)

        for b in s.get("bullets", []):
            add_body(doc, b, spec, bullet=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / cfg["output_filename"]
    doc.save(out)
    return out


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #
def verify(path: Path) -> bool:
    ok = True

    if zipfile.ZipFile(path).testzip() is not None:
        print(f"[FAIL] {path.name}: corrupt zip")
        return False
    print("[ok]  zip integrity")

    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")

    try:
        from lxml import etree  # type: ignore
        etree.fromstring(xml.encode("utf-8"))
        print("[ok]  XML well-formed")
    except ImportError:
        print("[skip] lxml not installed; skipping well-formedness check")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] malformed XML: {exc}")
        ok = False

    import re
    for m in re.finditer(r"<w:pPr>(.*?)</w:pPr>", xml, re.S):
        inner = m.group(1)
        if "w:spacing" in inner and "w:ind" in inner:
            if inner.index("w:spacing") > inner.index("w:ind"):
                print("[FAIL] w:ind precedes w:spacing (Word will reject this file)")
                ok = False
            break
    else:
        print("[warn] no paragraph with both spacing and indent found")
    if ok:
        print("[ok]  pPr child order")

    try:
        from docx import Document as D
        n = len(D(str(path)).paragraphs)
        print(f"[ok]  round-trip ({n} paragraphs)")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] cannot reopen: {exc}")
        ok = False

    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="YAML or JSON resume config")
    ap.add_argument("--out", default="./out", help="output directory")
    ap.add_argument("--verify", action="store_true", help="run structural checks")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    raw = cfg_path.read_text(encoding="utf-8")
    cfg = yaml.safe_load(raw) if cfg_path.suffix in {".yaml", ".yml"} else __import__("json").loads(raw)

    out = build(cfg, Path(args.out))
    print(f"[built] {out}")

    if args.verify and not verify(out):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
