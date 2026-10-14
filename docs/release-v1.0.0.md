# v1.0.0 — Initial release

> Copy everything below the divider into the GitHub release body.
> Tag: `v1.0.0` · Title: `v1.0.0 — Initial release`

---

## job-hunt-workflow v1.0.0

An agent skill for running a graduate or internship job search end-to-end.

### What's included

**Five-stage pipeline**

1. **Collect** — JD sources, text extraction from `.docx` / `.pages` / `.pdf` / `.html`, and
   decomposition into a structured requirement list.
2. **Tailor** — one resume per JD, built by mapping each JD requirement to the strongest real
   evidence. Fabrication is structurally disallowed: no evidence means an honest recorded gap.
3. **Format** — two layout profiles (`modern`, `ats`) with exact parameters, plus the OOXML traps
   that silently corrupt Word files.
4. **Apply** — resolving the canonical portal (with ATS recognition), and an assisted prefill
   workflow with hard safety guardrails.
5. **Track & Prepare** — tracker schema and status vocabulary, plus structured prep for
   psychometrics, recorded video interviews and manager interviews.

**Scripts**

| Script | Purpose |
|---|---|
| `extract_text.py` | `.docx` / `.pages` / `.pdf` / `.html` → text; standard-library-only for DOCX and Pages |
| `build_resume.py` | config → `.docx`, with built-in structural verification |
| `build_tracker.py` | config → `.xlsx` tracker with dropdowns, colour fills and deadline highlighting |
| `scan_pii.py` | personal-data scan to run before publishing or sharing |
| `check_skill.py` | frontmatter, YAML, link and compile checks for this repository |

**Templates** — placeholder-only starting points for the candidate profile, resume config, tracker
and autofill profile.

**Examples** — a fully de-identified walkthrough of the JD-mirroring method, plus a real generated
sample resume (`examples/sample-output/`, config + `.docx` + `.pdf`).

**CI** — `.github/workflows/ci.yml` runs two jobs on every push and pull request:
`pii-guard` (dependency-free privacy gate) and `skill-check` (integrity across Python 3.10 and 3.12).

### Why this exists

Most "AI resume" tools stuff keywords. This one enforces a discipline:

**every JD requirement → the single strongest piece of evidence → one bullet written in the JD's own language.**

If there is no evidence, the workflow records an honest *gap* instead of inventing a bullet. An
invented bullet becomes an unanswerable interview question — which is why the honesty rule is
structural, not optional.

### Safety properties

- **No auto-submit path exists in the code.** The workflow prefills and hands the submit button back
  to the human, by design.
- **Credentials are never typed, stored or logged** by these scripts. You sign in yourself; the
  assistant works in the session you already have open.
- **No CAPTCHA or bot-check bypass.** The workflow stops and hands control back.
- **A PII scanner ships with the skill** and is expected to run before every push — CI enforces it.
- **No personal data in this repository.** Every example, template and script uses placeholders only.

### Requirements

```
python-docx>=1.1.0
openpyxl>=3.1.0
PyYAML>=6.0
pypdf>=4.0
```

Python 3.10 or newer. See `requirements.txt`.

### Verification

All scripts are exercised before release:

- `build_resume.py --verify` passes zip integrity, XML well-formedness, `pPr` child ordering and
  round-trip checks
- `extract_text.py` is validated against `.docx` and `.pages` fixtures
- `scan_pii.py` is validated both ways: it must flag real PII, and must pass this repository
- `check_skill.py` passes frontmatter, YAML, link and compile checks

### Getting started

```bash
mkdir -p private
cp templates/candidate-profile.example.yaml private/candidate-profile.yaml
cp templates/resume-config.example.yaml    private/resume-config.yaml
cp templates/tracker.example.yaml          private/tracker.yaml

python scripts/extract_text.py path/to/jd.docx --out private/jds/
python scripts/build_resume.py private/resume-config.yaml --out private/out/ --verify
python scripts/build_tracker.py private/tracker.yaml --out private/out/tracker.xlsx
```

Keep `private/` git-ignored. It is already covered by the shipped `.gitignore`.

### Known limitations

- `.pages` extraction is **lossy** — text split across protobuf message boundaries can be dropped.
  Verify anything you intend to quote. Documented in `references/01-collect-jds.md`.
- `scan_pii.py` is a heuristic gate, not a guarantee. It reduces the chance of an accidental leak;
  it does not prove absence.
- Form autofill is deliberately **assisted, not automatic** (see `references/05-autofill-webforms.md`).
- The `modern` profile's photo anchoring is tuned for Word; other renderers may shift it.

### Licence

MIT — see [LICENSE](../LICENSE).

### Acknowledgements

The JD → evidence mapping discipline draws on how career-operations tooling frames
requirement-level matching: map each requirement to concrete evidence rather than stacking
experience or stuffing keywords.
