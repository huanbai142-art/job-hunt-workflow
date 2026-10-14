# Stage 4a — Find the official application portal

Goal: for each JD, resolve the **canonical apply path**, not the first link that looks plausible.
Applying through the wrong channel is a silent rejection.

## Resolution order

1. **Employer careers site** — search `site:<employer-domain> careers` or navigate
   `<employer-domain>/careers`. The posting's own "Apply" button is authoritative.
2. **The ATS tenant** — most large employers route applications through a hosted ATS. Recognising the
   tenant tells you what the form will look like:

   | Tenant | URL pattern | Notes |
   |---|---|---|
   | Workday | `*.myworkdayjobs.com` | Long multi-step form, account required, often asks for history in detail |
   | Greenhouse | `boards.greenhouse.io/<company>` | Short form, resume-first |
   | Lever | `jobs.lever.co/<company>` | Short form, resume-first |
   | Taleo / Oracle | `*.taleo.net` | Legacy, fragile, long forms |
   | SuccessFactors | `*.successfactors.com` | Enterprise, account required |
   | 北森 (Beisen) | `*.beisen.com` / `*.zhiye.com` | Common for Chinese campus recruiting |
   | Moka | `app.mokahr.com` | Common for Chinese tech firms |
   | SmartRecruiters | `jobs.smartrecruiters.com` | Short form |

3. **Official campus-recruiting site** — many programs have a dedicated campus portal separate from
   the experienced-hire site. Campus roles are frequently *only* on the campus portal.
4. **Aggregators** (LinkedIn, Indeed, 猎聘, BOSS直聘, 实习僧, 牛客) — use for discovery and for the
   JD text, then **always** follow through to the employer's own apply link. Never assume an
   aggregator's "apply" form reaches the employer.

## Verifying a link is genuine

- The domain matches the employer's corporate domain, or a known ATS tenant they use.
- The requisition ID in the URL appears on the employer's own site too.
- The posting is not expired (check the posted/closing date).
- The page does not ask for anything unusual (payment, ID scan, bank details) at the discovery stage.

Flag anything that fails these checks to the user rather than proceeding.

## Capturing what matters for later

For each JD, record:

```yaml
portal:
  employer: "{{EMPLOYER}}"
  apply_url: "https://..."
  ats: "workday"            # from the table above, or "custom"
  account_required: true
  steps_estimate: 5         # rough number of form pages
  requires:
    - resume_pdf
    - transcript
    - photo
    - english_cv
  notes: "campus portal separate from experienced-hire site; caps at 3 roles"
```

The `requires` list feeds directly into the prefill plan in
[05-autofill-webforms.md](05-autofill-webforms.md): gather the documents once, reuse them everywhere.

## Common document asks (prepare once, reuse)

- Resume in the format the portal accepts (PDF unless it says otherwise).
- Transcript / degree certificate, sometimes with an official stamp.
- English-language CV, when the posting is bilingual.
- A photo, for employers that expect one.
- Standard answers: expected graduation date, availability window, salary expectation, referral
  source, and a self-introduction paragraph in both languages.

Keep these in one private folder so every application is assembled from the same set.

## Ethics and platform rules

- Use the employer's channel. Bypassing a portal, or applying through a third party that is not
  authorised, invalidates the application and can get a candidate blacklisted.
- Respect each site's terms of service and `robots.txt`. Where a site disallows automated access,
  do not automate it — do the assisted workflow in
  [05-autofill-webforms.md](05-autofill-webforms.md) instead.
- Do not scrape personal data about recruiters or other candidates.
