---
name: job-hunt-workflow
description: Run an end-to-end graduate/campus job-application workflow — collect target job descriptions (JDs), tailor a resume to each JD with a professional resume-writer process (JD-requirement → evidence mapping, STAR/CAR, no fabrication), locate official application portals/ATS entry points, assist with semi-automated online-application form filling (prefill only, never auto-submit), maintain an application tracker, and prepare for assessments and interviews. Use when the user asks to gather job postings, rewrite/tailor a resume for a specific job, find where to apply, autofill or prefill an online application form, keep an application tracker, or prepare for a hiring assessment, online test, or interview.
license: MIT
metadata:
  version: "1.0"
  author: job-hunt-workflow contributors
  compatibility: "SKILL.md frontmatter format (Anthropic Agent Skills / DSH / compatible agent runtimes)"
---

# Job Hunt Workflow

A five-stage, reusable pipeline for running a graduate or internship job search at scale.
It turns "apply to 100 roles" from an exhausting manual grind into a repeatable process that
stays honest, stays on-brand, and never invents experience.

The pipeline:

| Stage | Goal | Reference |
|---|---|---|
| 1. Collect | Gather and normalize target JDs into a structured form | [references/01-collect-jds.md](references/01-collect-jds.md) |
| 2. Tailor | Rewrite one resume per JD using JD → evidence mapping | [references/02-tailor-resume.md](references/02-tailor-resume.md) |
| 3. Format | Produce a clean, ATS-safe, recruiter-ready document | [references/03-resume-formatting.md](references/03-resume-formatting.md) |
| 4. Apply | Find the official portal and assist with form filling | [references/04-find-portals.md](references/04-find-portals.md), [references/05-autofill-webforms.md](references/05-autofill-webforms.md) |
| 5. Track & Prepare | Keep a pipeline tracker; prep assessments and interviews | [references/06-track-applications.md](references/06-track-applications.md), [references/07-interview-prep.md](references/07-interview-prep.md) |

Supporting material you will need along the way:

- Cover letters, application emails, and open-question answers —
  [references/08-cover-letter.md](references/08-cover-letter.md)

## Core rules (apply to every stage)

1. **Never fabricate.** Every resume bullet must trace to something the candidate actually did.
   If a JD requirement has no matching evidence, say so and mark it a gap — do not paper over it.
2. **Mirror the JD's language, do not stack keywords.** For each JD requirement, produce the
   single strongest piece of evidence and rewrite it in the JD's own vocabulary. One requirement,
   one bullet. See [references/02-tailor-resume.md](references/02-tailor-resume.md).
3. **Protect personal data.** Never commit real personal information into this skill, into example
   files, or into a public repository. All examples and templates use placeholders only.
   Keep the candidate's real data in a private, git-ignored file outside the skill.
4. **Never auto-submit an application.** Prefill, then hand control back to the human. See the
   guardrails in [references/05-autofill-webforms.md](references/05-autofill-webforms.md).
5. **One resume, one JD.** A generic resume is a weak resume. Tailor per posting.
6. **Verify before delivering.** Render, open, and (where possible) visually check every document
   before telling the user it is ready.

## Personal-data handling (read this first)

This skill is designed to be publishable. Treat it as public at all times.

- Real candidate data lives in a **private profile file** (e.g. `candidate-profile.yaml`) that is
  listed in `.gitignore`. Ship only `templates/candidate-profile.example.yaml`.
- Before any commit or share, run the PII scan:
  `python scripts/scan_pii.py <path>` — it flags names, phone numbers, emails, ID numbers, URLs,
  and common personal-data patterns.
- Placeholders used throughout: `{{FULL_NAME}}`, `{{PHONE}}`, `{{EMAIL}}`, `{{UNIVERSITY}}`,
  `{{DEGREE}}`, `{{EMPLOYER}}`, `{{PROJECT_NAME}}`. Never replace them with real values inside
  this repository.

## Quick start

```bash
# 0. Dependencies
pip install python-docx openpyxl pypdf

# 1. Copy the profile template OUTSIDE the repo and fill in real data
cp templates/candidate-profile.example.yaml ./private/candidate-profile.yaml

# 2. Collect JDs (paste text, or point the extractor at a file)
python scripts/extract_text.py path/to/jd.docx --out ./private/jds/

# 3. Build a tailored resume from a config
python scripts/build_resume.py ./private/resume-config.yaml --out ./private/out/

# 4. Build (or refresh) the application tracker
python scripts/build_tracker.py ./private/tracker.yaml --out ./private/out/tracker.xlsx

# 5. Before publishing anything
python scripts/scan_pii.py . --fail-on-find
python scripts/check_skill.py
```

## Working with the JD at hand

Do not treat a JD as a blob of keywords. Parse it first:

1. Split the posting into **requirement units** (one sentence or clause each).
2. Classify each unit: `must-have`, `nice-to-have`, `responsibility`, `culture`.
3. For each unit, ask: *which single experience is the strongest evidence?*
4. Only then write. A requirement without evidence becomes an honest gap, not a fake bullet.

The full method, including worked before/after examples, is in
[references/02-tailor-resume.md](references/02-tailor-resume.md).

## Style guidance

- Match the requested language (Chinese, English, or bilingual). Default to the JD's language.
- Default to **one page** for early-career candidates.
- Two common layout profiles ship with this skill, both driven by `scripts/build_resume.py`:
  - `modern` — a clean corporate look with a photo, thin underlined section heads, right-aligned
    dates, and a bold keyword line. Common for mainland-China campus recruiting.
  - `ats` — a photo-free, single-column, high-contrast layout tuned for parsers and conservative
    employers.
  Pick per employer; never mix.

## Deliverables checklist

- [ ] One tailored resume per JD (source config preserved for re-editing)
- [ ] A tracker row per application (company, role, resume version, status, deadline, notes)
- [ ] Interview/assessment prep notes for any active pipeline
- [ ] PII scan clean before any share or publish
