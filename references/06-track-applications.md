# Stage 5a — Track the pipeline

Goal: never lose a deadline, never apply twice to the same posting, and always know what the next
action is.

## The tracker schema

One row per application. Minimum viable columns:

| Column | Meaning |
|---|---|
| `company` | Employer name |
| `role` | Role title as posted |
| `resume_version` | Filename or version tag of the resume actually submitted |
| `status` | Current stage (controlled vocabulary — see below) |
| `channel` | Where it was applied (careers site, ATS tenant, campus portal, referral) |
| `deadline` | Closing date, if any |
| `applied_on` | Date submitted |
| `next_action_on` | Date the next step is expected |
| `next_action` | What that step is |
| `link` | Canonical posting URL |
| `notes` | Anything else |

## Status vocabulary

Keep it closed and short, so the sheet stays sortable:

`待投` → `已投` → `测评中` → `测评完成` → `面试中` → `Offer` / `已拒` / `无回应`

(`to_apply` → `applied` → `assessment_pending` → `assessment_done` → `interviewing` → `offer` /
`rejected` / `no_response`)

Every status change should also set `next_action` — a status with no next action is a row that will
be forgotten.

## Build it

`scripts/build_tracker.py` generates the workbook from a YAML/CSV source:

- header row frozen and filtered,
- a dropdown validator on `status` bound to the vocabulary above,
- conditional colour fills per status,
- a `deadline` column that highlights imminent or overdue dates,
- optional per-stage summary counts.

```bash
python scripts/build_tracker.py ./private/tracker.yaml --out ./private/out/tracker.xlsx
```

## Operating the tracker

- **Weekly review.** Walk every row: what is the next action, and is it scheduled? Rows with no next
  action get one.
- **Deadline sweep.** Sort by `deadline`; anything within seven days gets priority over new
  applications.
- **Resume-version audit.** A row whose `resume_version` does not match the file actually sent is a
  bug — fix it, because you will be asked about your resume in the interview.
- **Stale-row rule.** No movement after the employer's stated timeline plus a week → mark
  `no_response` and move on. Chasing is time-boxed, not indefinite.
- **Caps.** Enforce the program's application limits (recorded in the JD notes) at the point of
  adding a row, not after.

## Evidence to keep

For each application, keep (in private storage, never in the repository):

- the resume actually submitted,
- the JD snapshot (see [01-collect-jds.md](01-collect-jds.md)) — postings vanish,
- the confirmation reference,
- a note of which requirements you chose to emphasise, so interview prep and the resume agree.

## Why the archive matters

The single most common self-inflicted interview wound is not remembering what your own resume said.
An archive that pairs each submitted resume with its JD snapshot and emphasis notes makes preparation
mechanical.

## Sample roll-up

```
Status                Count
待投                    12
已投                     0
测评中                    3
测评完成                  5
面试中                    2
Offer                    0
已拒                     4
无回应                    6
```

Print this at each weekly review. If `待投` grows while `已投` stays flat, the bottleneck is the
application step, not the hunting step — fix the bottleneck, not the volume.
