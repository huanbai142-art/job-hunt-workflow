# Publishing this skill on GitHub

Ready-to-paste metadata, so the repository looks deliberate rather than dumped.

---

## Repository name

```
job-hunt-workflow
```

Alternatives, if that is taken:

| Name | Feel |
|---|---|
| `job-hunt-workflow` | Recommended — descriptive, discoverable, no hype |
| `campus-job-hunt-skill` | Emphasises the campus/graduate niche |
| `jd-tailored-resume` | Narrows to the strongest single feature |
| `job-hunt-agent-skill` | Emphasises the agent-skill packaging |

## Short description (the GitHub "About" field, ≤160 chars)

```
An agent skill that runs a job search end-to-end: collect JDs, tailor a resume per JD, find the apply portal, prefill forms, track and prep. No fabrication.
```

Shorter variant:

```
Agent skill for job hunting: JD collection, per-JD resume tailoring, portal discovery, assisted form filling, tracking and interview prep.
```

## Topics

```
agent-skill  claude-skill  skill  job-search  job-hunting  resume  resume-builder
ats  cover-letter  career  docx  python  openpyxl  campus-recruiting  graduate-jobs
```

Pick roughly 10–14. The first four drive discovery; the rest aid filtering.

## Suggested repository settings

- **Visibility**: public
- **License**: MIT (already included)
- **Default branch**: `main`
- **Issues**: enabled — people will want to report JD formats that fail to parse
- **Discussions**: optional, useful for "show your tailored resume" threads
- **Topics**: as above
- **Social preview**: a screenshot of a built resume, with the name and contact details blurred

## Release — v1.0.0

**Tag:** `v1.0.0`
**Title:** `v1.0.0 — Initial release`

The release body is kept as a ready-to-paste file:
[`docs/release-v1.0.0.md`](docs/release-v1.0.0.md). Open it, copy everything below the divider,
and paste it into the GitHub release form. The same text is reproduced inline below so this file
stands alone.

```markdown
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
- `extract_text.py` — `.docx` / `.pages` / `.pdf` / `.html` → text, standard-library-only for DOCX
  and Pages
- `build_resume.py` — config → `.docx`, with built-in structural verification
- `build_tracker.py` — config → `.xlsx` tracker with dropdowns, colour fills and deadline highlighting
- `scan_pii.py` — personal-data scan to run before publishing or sharing

**Templates** — placeholder-only starting points for the candidate profile, resume config, tracker
and autofill profile.

**Examples** — a fully de-identified walkthrough of the JD-mirroring method.

### Safety properties

- No auto-submit path exists in the code.
- Credentials are never typed, stored or logged by these scripts.
- No CAPTCHA or bot-check bypass; the workflow stops and hands control back.
- A PII scanner ships with the skill and is expected to be run before every push.

### Requirements

`python-docx`, `openpyxl`, `PyYAML`, `pypdf` — see `requirements.txt`.

### Verification

All scripts are exercised by the maintainers before release:
- `build_resume.py --verify` passes zip integrity, XML well-formedness, `pPr` child ordering and
  round-trip checks
- `extract_text.py` is validated against `.docx` and `.pages` fixtures
- `scan_pii.py` is validated both ways: it must flag real PII, and must pass this repository

### Licence

MIT
```

## Suggested README badges

Insert directly under the `# job-hunt-workflow` heading:

```markdown
![CI](https://github.com/OWNER/job-hunt-workflow/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![skill](https://img.shields.io/badge/agent--skill-SKILL.md-green)
![no auto-submit](https://img.shields.io/badge/auto--submit-never-critical)
```

Replace `OWNER` with your GitHub username. **The CI badge 404s until the workflow has run at least
once**, so push first, then confirm the badge renders.

The last badge is not decoration — it is the design commitment a reader most wants to confirm.

## CI behaviour to expect

`.github/workflows/ci.yml` triggers on push to `main`, on every pull request, and manually.

| Job | Purpose | Failure means |
|---|---|---|
| `pii-guard` | Personal-data and artefact gate | Real data, or a build artefact, reached the tracked tree |
| `skill-check` | Frontmatter, YAML, links, compile, smoke tests | The skill is malformed or a shipped script is broken |

`pii-guard` is intentionally dependency-free. If it could fail to install, it could be skipped, and
a privacy gate that can be skipped is not a gate.

### If `pii-guard` fails on a legitimate file

The check is heuristic. A false positive on a file that genuinely must be tracked should be handled
by narrowing the pattern in `scripts/scan_pii.py` — **not** by deleting the CI step. Record the
narrowing as a comment explaining why, so the next maintainer does not silently re-tighten it.

### If `skill-check` fails

Run the same command locally; the output is identical:

```bash
python scripts/check_skill.py
```

The finding names the file and the problem, so it is usually self-explanatory.

## Recommended branch protection

Once the first run is green, protect `main` so the gate cannot be bypassed:

- require status checks: `pii-guard` and the `skill-check` matrix entries
- require a pull request before merging
- do not allow force pushes to `main`

This is what makes the privacy promise structural rather than aspirational.

## First-push checklist

```bash
cd job-hunt-workflow
python scripts/scan_pii.py . --fail-on-find     # must exit 0
python scripts/check_skill.py                   # must exit 0
git init
git add .
git commit -m "feat: job-hunt-workflow skill v1.0.0"
git branch -M main
git remote add origin git@github.com:<you>/job-hunt-workflow.git
git push -u origin main
git tag -a v1.0.0 -m "v1.0.0 — initial release"
git push origin v1.0.0
```

Then:

1. Confirm the `CI` workflow went green in the Actions tab.
2. Replace `OWNER` in the README badge URL and commit.
3. Create the release from the `v1.0.0` tag using the notes above.
4. Turn on branch protection with the required checks.

## Post-publish verification

- [ ] Browse the repository in a logged-out window; confirm no private file is visible.
- [ ] Click every relative link in `README.md` and `SKILL.md`; confirm none 404.
- [ ] Confirm `git ls-files` contains no `private/`, `.docx`, `.pdf` or `.xlsx`.
- [ ] Re-run `scan_pii.py` against the checked-out clone, not just the working copy.

```bash
# the definitive check: what actually got committed
git ls-files | grep -iE "private|\.docx$|\.pdf$|\.xlsx$|credential|secret" || echo "clean"
```
