# Stage 3 — Format the resume

Content wins interviews; formatting wins *readings*. A recruiter who cannot parse or cannot find the
message in eight seconds will not read the content.

This reference covers the two layout profiles shipped with the skill, the exact formatting
parameters to use, and the OOXML traps that silently corrupt Word files.

## Choosing a profile

| Profile | Use when | Characteristics |
|---|---|---|
| `modern` | Mainland-China campus recruiting, internet/manufacturing/consumer firms | Photo top-right, thin underlined section heads, right-aligned dates, bold keyword line under the name |
| `ats` | Conservative employers, banks/consulting, anything parsed by an ATS, or when the posting says "plain format" | No photo, single column, centered header block, dark-blue section heads with a hairline rule, no icons/progress bars/tables |

Never mix the two. If unsure, build `ats` and offer `modern` as an alternative.

## Profile `ats` — reference parameters

Page and spacing:

- Paper A4; margins 1.3 cm top/bottom, 1.5 cm left/right; header/footer 0.5 cm
- Line spacing **exact 14.5 pt** for body text; space before/after 0 pt
- Body justified; header block centered; section heads left-aligned

Type scale:

| Element | Font | Size | Weight | Colour |
|---|---|---|---|---|
| Name | 微软雅黑 / Source Han Sans | 18 pt | Bold | Black |
| Target-role line | 微软雅黑 | 10 pt | Bold | Black |
| Basic info lines | 微软雅黑 | 9 pt | Regular | Black |
| Section head | 微软雅黑 | 10.5 pt | Bold | RGB 31,78,121 (`#1F4E79`) |
| Company/project name | 微软雅黑 | 9.5 pt | Bold | Black |
| Body / bullets | 等线 (DengXian) or 微软雅黑 | 9 pt | Regular | Black |
| Dates | Arial | 9 pt | Regular | `#404040` |

Details:

- Section head carries a **0.5 pt** bottom rule in the same dark blue.
- Project name and date share one line; the date is right-aligned on a right tab at the text width.
- Bullets use a solid round marker (`•`), with a hanging indent so wrapped lines align.
- No photos, progress bars, icon fonts, or complex tables.
- If the document exceeds one page, delete the *core-course names* first — never shrink body text
  below 8 pt.

## Profile `modern` — reference parameters

- Name bold; subtitle and contact in grey `#888888`; keyword line in `#444444`
- Section heads: bold, 10 pt, near-black `#1A1A1A`, thin `0.5 pt` bottom rule via paragraph border
- Entry title bold 11 pt; date bold 10 pt grey, right-aligned on a right tab
- Body 10.5 pt, near-black `#1A1A1A`
- Photo: floating (anchored) top-right, ~2.6 cm wide, text wrapping *none*
- Skill block: bold label + regular value, labels padded so values align

## OOXML traps (these corrupt files — read before editing)

### 1. Element order inside `<w:pPr>` is schema-ordered

Word rejects a file whose paragraph-property children are out of order. The relevant order is:

```
pStyle, keepNext, keepLines, pageBreakBefore, framePr, widowControl, numPr,
suppressLineNumbers, pBdr, shd, tabs, ..., spacing, ind, ..., jc, ...
```

Concretely:

- `w:pBdr` (section-head rule) must come **before** `w:spacing`.
- `w:tabs` must come before `w:spacing`.
- `w:spacing` must come **before** `w:ind`.
- `w:jc` comes **after** both.

`python-docx` inserts its own properties in the correct order, but a manually appended element does
not. When you append by hand, insert at the correct position:

```python
pPr = p._p.get_or_add_pPr()
pBdr = pPr.makeelement(qn('w:pBdr'), {})   # build the border
pPr.insert(0, pBdr)                        # BEFORE any spacing/jc
# then set spacing via paragraph_format, or append it now
```

For bullets, set spacing **before** adding the indent:

```python
pf.line_spacing = Pt(14.5)      # writes w:spacing
pf.space_before = Pt(0)
pf.left_indent = Cm(0.5)        # writes w:ind — must come after spacing
```

Verify after generating:

```python
import re
xml = zipfile.ZipFile(path).read('word/document.xml').decode('utf-8')
for m in re.finditer(r'<w:pPr>(.*?)</w:pPr>', xml):
    s = m.group(1)
    if 'w:ind' in s and 'w:spacing' in s:
        assert s.index('w:spacing') < s.index('w:ind'), 'spacing must precede ind'
        break
```

### 2. East-Asian fonts need `w:eastAsia`

`run.font.name = "微软雅黑"` sets only the Latin (`w:ascii` / `w:hAnsi`) typeface. CJK glyphs fall
back to whatever the theme provides. Set the East-Asian attribute explicitly:

```python
rFonts = run._r.get_or_add_rPr().get_or_add_rFonts()
rFonts.set(qn('w:eastAsia'), '微软雅黑')
rFonts.set(qn('w:ascii'), 'Microsoft YaHei')
rFonts.set(qn('w:hAnsi'), 'Microsoft YaHei')
```

### 3. Exact line spacing clips large text

With `exact` line spacing, a font larger than the line box is vertically clipped. A 18 pt name in a
14.5 pt exact line loses its top and bottom. Give oversized runs a larger line height:

```python
pf.line_spacing = Pt(24)          # for the 18 pt name
pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
```

### 4. Floating images are anchors, not inline shapes

`python-docx` only creates inline pictures. A photo that floats top-right and does not push text is a
`<wp:anchor>` with `<wp:wrapNone/>`:

```python
rid, _ = doc.part.get_or_add_image('photo.png')
anchor = (
    '<wp:anchor xmlns:wp=".../wordprocessingDrawing" xmlns:a=".../drawingml/2006/main" '
    'xmlns:pic=".../drawingml/2006/picture" '
    'xmlns:r=".../officeDocument/2006/relationships" '
    'distT="0" distB="0" distL="114300" distR="114300" simplePos="0" '
    'relativeHeight="251659264" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
    '<wp:simplePos x="0" y="0"/>'
    '<wp:positionH relativeFrom="column"><wp:posOffset>5029200</wp:posOffset></wp:positionH>'
    '<wp:positionV relativeFrom="paragraph"><wp:posOffset>34290</wp:posOffset></wp:positionV>'
    '<wp:extent cx="936625" cy="1368425"/><wp:effectExtent l="0" t="0" r="3175" b="3175"/>'
    '<wp:wrapNone/><wp:docPr id="1" name="Picture 1"/>'
    '<a:graphic><a:graphicData uri=".../drawingml/2006/picture"><pic:pic>'
    '<pic:nvPicPr><pic:cNvPr id="0" name="photo.png"/><pic:cNvPicPr/></pic:nvPicPr>'
    '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
    '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="936000" cy="1368000"/></a:xfrm>'
    '<a:prstGeom prst="rect"/></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:anchor>'
) % rid
run = paragraph.add_run()
run._r.append(parse_xml('<w:drawing xmlns:w=".../wordprocessingml/2006/main">' + anchor + '</w:drawing>'))
```

If the employer expects `ats`, skip the photo entirely.

### 5. Bullet markers

A literal `•` with a hanging indent is the most portable choice. Do **not** depend on Word's list
numbering (`numbering.xml`) unless you ship the definition — an ATS may render the marker as a box
or drop it. Hanging indent:

```python
pf.left_indent = Cm(0.5)
pf.first_line_indent = Cm(-0.5)   # the marker sits in the hanging space
```

## Verification before delivery

1. **Package integrity** — `unzip -t file.docx` must report no errors.
2. **Well-formed XML** — parse `word/document.xml` with `lxml.etree.fromstring`.
3. **Property order** — assert `w:spacing` precedes `w:ind` (see trap 1).
4. **Round-trip** — reopen with `python-docx` and confirm paragraph counts.
5. **Text fidelity** — extract the text and confirm nothing was mangled.
6. **Length** — confirm it is one page (or the agreed count) via PDF page count.
7. **Visual check** — render a preview and inspect it when image input is available.

`scripts/build_resume.py` performs steps 1–5 automatically and prints a report.

## Producing a PDF

The `.docx` is the editable deliverable; the PDF is what most portals accept. Preferred order:

1. The candidate's own word processor ("Save as PDF") — uses the exact fonts they see.
2. A headless browser rendering an HTML mirror of the layout, if the word processor is unavailable.

Note the font-substitution caveat: if the file specifies Windows fonts (微软雅黑 / 等线) and the
conversion host is macOS or Linux, those fonts are absent and the renderer substitutes them. The
`.docx` still carries the correct font names for anyone who opens it on the target platform; the PDF
bakes in whatever was substituted. Tell the user this rather than letting them discover it.

Always confirm the PDF page count matches the intent before delivering.
