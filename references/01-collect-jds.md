# Stage 1 — Collect and normalize JDs

Goal: turn scattered postings — screenshots, pasted text, `.docx`/`.pages`/`.pdf` files, web pages —
into a consistent, machine-readable form you can reason over.

## Sources

Prefer, in order:

1. **The employer's own careers site** — the authoritative text and the canonical apply link.
2. **Official campus-recruiting portals / ATS tenants** (Workday, Greenhouse, Lever, Taleo, 北森,
   Moka, 智联/BOSS/实习僧 listings that link back to the employer).
3. **Aggregators and campus boards** — useful for discovery, but always resolve back to the source
   before applying, because aggregator text is often truncated or stale.

Record for every JD: employer, role title, business unit, location, posting URL, deadline,
source, and the date you captured it. Postings change without notice, so the capture date matters.

## Extracting text from common file types

`scripts/extract_text.py` handles these. Notes on each:

### `.docx`

Read `word/document.xml` from the zip and collect `w:t` text nodes in document order. Preserve
paragraph breaks (`w:p` boundaries) and table cells where present — a JD is often laid out in a table.
For simple text extraction, avoid pulling in a heavyweight library; the zip-and-parse route has no
dependencies.

### `.pages` (Apple Pages)

A `.pages` file is a zip. The body text lives in `Index/Document.iwa`, which is a protobuf stream,
not plain text. A pragmatic extraction: read the bytes, decode as UTF-8 with errors ignored, and
collect runs of CJK/Latin characters.

Two caveats worth knowing:

- Some characters are split across message boundaries and are lost or replaced by stray bytes, so the
  extraction is *lossy*. Never treat it as the authoritative text — always cross-check against the
  original rendering for anything you will quote.
- Long contiguous passages survive well; short single-character fragments may not.

If the file is `.pages` but has a `.docx` extension (a common export accident), detect it by
inspecting the zip contents for `Index/` rather than trusting the suffix.

### `.pdf`

Use a text-extraction library (`pypdf`). If the PDF is a scan, fall back to OCR, and flag to the user
that OCR text may contain errors worth proofreading.

### Pasted text / screenshots

Ask for the text where possible. If only an image is available, OCR it and mark it as *unverified*.

## Normalizing into a requirement list

Convert the raw text into the structure the tailoring stage consumes:

```yaml
jd:
  employer: "{{EMPLOYER}}"
  role: "{{ROLE}}"
  unit: "{{BUSINESS_UNIT}}"
  location: "{{LOCATION}}"
  url: "https://example.com/job/123"
  captured_at: "YYYY-MM-DD"
  deadline: "YYYY-MM-DD"      # or null
  source: "employer careers site"
  requirements:
    - id: R1
      text: "<requirement, near-verbatim>"
      type: must_have          # must_have | nice_to_have | responsibility | culture
    - id: R2
      text: "<requirement>"
      type: responsibility
  responsibilities:
    - "<duty>"
  notes: "<apply limits, referral rules, assessment stage, etc.>"
```

Rules for the split:

- One **requirement unit** per sentence or clause. Do not merge separate asks.
- Keep the employer's wording in `text`; the tailoring stage mirrors it.
- Mark the type honestly — `must_have` vs `nice_to_have` changes how you allocate resume space.
- Capture logistics (application caps, "first choice preferred", assessment stages, deadlines) in
  `notes`; they drive the tracker and the prep plan.

## Application-limit warnings

Many campus programs cap how many roles you may apply to and how many may be in process at once, and
some give preference to a first choice. Always surface these constraints to the user **before**
building a batch of resumes — a wasted application slot is expensive.

## Sanity checks before moving on

- [ ] Every JD has a canonical URL and a capture date.
- [ ] Deadlines are recorded, and any that have passed are flagged.
- [ ] Requirement units are split, not merged.
- [ ] Logistics and caps are captured in `notes`.
- [ ] Anything extracted from a lossy source is marked as needing verification.
