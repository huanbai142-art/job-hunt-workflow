# Stage 4b — Assisted web-form filling (prefill only)

Goal: remove the tedium of re-typing the same facts into every portal, **without** ever submitting on
the candidate's behalf or breaking a platform's rules.

> **Non-negotiable:** the agent prefills; the human reviews and submits. There is no auto-submit path
> in this skill, and there should not be one. A wrong-but-submitted application is worse than a slow
> one, and many portals prohibit automated submission outright.

## The three modes (choose the least invasive that works)

### Mode A — Prepared answers (always safe, always available)

Do not touch the browser at all. Assemble a "form pack": every standard field pre-answered in a
private document, so the candidate copy-pastes.

```yaml
# private/autofill-profile.yaml  (git-ignored — contains personal data)
identity:
  full_name: "{{FULL_NAME}}"
  preferred_name: "{{PREFERRED_NAME}}"
  phone: "{{PHONE}}"
  email: "{{EMAIL}}"
  city: "{{CITY}}"
education:
  - school: "{{UNIVERSITY}}"
    degree: "{{DEGREE}}"
    major: "{{MAJOR}}"
    start: "YYYY.MM"
    end: "YYYY.MM"
    gpa_or_rank: "{{RANK}}"
standard_answers:
  expected_graduation: "YYYY.MM"
  availability: "{{AVAILABILITY}}"
  salary_expectation: "{{SALARY_EXPECTATION}}"
  how_did_you_hear: "{{REFERRAL_SOURCE}}"
  self_intro_zh: "{{SELF_INTRO_ZH}}"
  self_intro_en: "{{SELF_INTRO_EN}}"
documents:
  resume_pdf: "private/docs/resume.pdf"
  transcript: "private/docs/transcript.pdf"
  english_cv: "private/docs/cv_en.pdf"
  photo: "private/docs/photo.jpg"
```

This mode has zero legal or account risk and covers most of the time savings. **Default to it.**

### Mode B — Browser-assisted prefill with the human in the loop

When the user explicitly asks for browser help and the site permits it:

1. The **human signs in**. The agent never handles credentials (see below).
2. The agent reads the current page, maps visible form fields to the profile, and reports a plan:
   *"I can fill 12 of 14 fields; 2 need your judgement."*
3. On approval, the agent fills only text inputs, selects, and file pickers — **never** the submit
   button, never a "declaration/consent" checkbox without explicit confirmation.
4. The agent stops and hands over: *"Filled. Please review fields 6 and 11, then submit yourself."*

Rules for this mode:

- **Never auto-submit.** Not even if asked mid-run; surface the request for explicit confirmation.
- **Never bypass CAPTCHAs, bot checks, rate limits, or paywalls.** If one appears, stop and hand over.
- **Never create accounts** on the candidate's behalf without explicit per-site instruction.
- **One site at a time**, human-paced. No parallel bulk submissions.
- **Stop on any mismatch** between the profile and the form; do not guess.
- Redact secrets from logs and screenshots.

### Mode C — Bulk automation

**Out of scope.** Bulk automated submission across many employers is against most portals' terms,
frequently detectable, and can burn a candidate's reputation across a whole sector. If the user asks
for it, explain the risk and offer Mode A or B instead.

## Credentials: how to handle them

- The skill ships with **no credentials and no credential storage**.
- Never type a password into a form on the user's behalf. The user signs in; the agent works in the
  already-authenticated session.
- If a workflow genuinely needs a secret, read it from the environment or the OS keychain at runtime:

  ```python
  import os
  token = os.environ["JOB_PORTAL_TOKEN"]   # never hardcode, never commit
  ```

- Never write credentials, session cookies, or tokens to disk, logs, screenshots, or the repository.
- Add `private/`, `*.env`, and `*credential*` to `.gitignore`.

## Field-mapping pitfalls

- **Date formats differ per portal** (`YYYY-MM`, `MM/YYYY`, `YYYY-MM-DD`). Keep the canonical value in
  the profile and convert per form.
- **Name order**: `family name` / `given name` are separate fields on Western ATS tenants. Do not
  guess from a single "name" string — ask once, store both.
- **Education history** on Workday-style forms often wants every institution, with dates and
  credentials, entered in reverse-chronological order.
- **Degree equivalences** differ by country; store the local name and the English name.
- **File-upload limits**: check the accepted type and size before uploading; a failed silent upload is
  a common rejection cause.
- **Required-but-hidden fields** only surface on validation. After filling, trigger the form's own
  validation and report what remains.

## Post-fill checklist (hand back to the human)

- [ ] Every required field is filled or explicitly marked as needing the candidate.
- [ ] Uploaded files are the right version for *this* employer.
- [ ] Screening questions answered truthfully (these are often the actual filter).
- [ ] Declaration/consent boxes reviewed by the human.
- [ ] Resume version recorded in the tracker against the application.
- [ ] **The human clicks submit.**

## After submission

- Record the submission date, the confirmation/requisition ID, and the resume version in the tracker.
- Save the confirmation email or screenshot reference (not the credentials).
- Note any promised next step and its timing, so the tracker can flag a follow-up.
