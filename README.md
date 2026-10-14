# job-hunt-workflow

![CI](https://github.com/huanbai142-art/job-hunt-workflow/actions/workflows/ci.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![skill](https://img.shields.io/badge/agent--skill-SKILL.md-green)
![no auto-submit](https://img.shields.io/badge/auto--submit-never-critical)

An agent skill for running a **graduate / internship job search end-to-end** — collect the job
descriptions, tailor a resume to each one, find the official application portal, assist with the
online form (never auto-submitting), track the pipeline, and prepare for the assessments and
interviews that follow.

It is designed to be **published and shared**. It ships with no personal data: every example,
template and script uses placeholders only — and CI enforces that on every push.

[中文说明](#中文说明) · [English](#english)

---

## English

### What it does

| Stage | Outcome |
|---|---|
| **1. Collect** | Target JDs turned into a structured requirement list (`.docx` / `.pages` / `.pdf` / web / pasted text) |
| **2. Tailor** | One resume per JD, built by mapping each JD requirement to the strongest real evidence — no fabrication, no keyword stuffing |
| **3. Format** | A recruiter-ready, parser-safe document in one of two layout profiles (`modern`, `ats`) |
| **4. Apply** | The canonical portal resolved, plus an assisted prefill workflow with hard safety guardrails |
| **5. Track & Prepare** | A status tracker workbook, and structured prep for psychometrics, video interviews and manager interviews |

### Why it is different

Most "AI resume" tools stuff keywords. This one enforces a discipline:

**every JD requirement → the single strongest piece of evidence → one bullet written in the JD's own language.**

If there is no evidence, the workflow records an honest *gap* instead of inventing a bullet.
An invented bullet becomes an unanswerable interview question — which is why the honesty rule is
structural, not optional.

### What you get

A real, generated sample ships in [`examples/sample-output/`](examples/sample-output/) — open the
[PDF](examples/sample-output/sample-resume-ats.pdf) to see the `ats` layout. Its content is
placeholder-only, and it was produced by the shipped script from the shipped config:

```
examples/sample-output/
  sample-config.yaml         the input
  sample-resume-ats.docx     the generated document (editable)
  sample-resume-ats.pdf      the same document, rendered
```

Regenerate it yourself:

```bash
python scripts/build_resume.py examples/sample-output/sample-config.yaml \
       --out /tmp/demo --verify
```

The `ats` layout, structurally:

```
            示例候选人 Example Candidate              <- 18pt bold, centred
     Example University ｜ MSc ｜ 20XX.XX 毕业        <- 9pt, centred
        {{PHONE}} ｜ {{EMAIL}} ｜ CET-6 558           <- 9pt, centred
     申请岗位：数据分析实习生 ｜ Example Corp          <- 10pt bold, centred
──────────────────────────────────────────────────  <- 0.5pt rule, #1F4E79
 个人概述                                            <- 10.5pt bold, dark blue
    <justified paragraph>
──────────────────────────────────────────────────
 教育背景
   Example University ｜ 数字经济学硕士      20XX.XX—20XX.XX   <- right-aligned date
     核心课程：…
──────────────────────────────────────────────────
 数据分析与项目经历
   示例研究项目 ｜ 数据分析负责人            20XX.XX—20XX.XX
     •  主导问卷设计与实地调研，用 Python 完成数据清洗…      <- justified bullets
──────────────────────────────────────────────────
```

Two layout profiles ship with it — `ats` (above) and `modern` (photo top-right, thin underlined
heads). See [references/03-resume-formatting.md](references/03-resume-formatting.md) for exact
parameters of both.

### Install

This is a `SKILL.md`-based skill, compatible with agent runtimes that read the
Anthropic Agent Skills / `SKILL.md` frontmatter convention.

```bash
git clone <this-repo> job-hunt-workflow
# then point your agent runtime's skill directory at it, or copy it into
# the runtime's skills folder.
```

### Requirements

```bash
pip install python-docx openpyxl pyyaml pypdf    # see requirements.txt
```

`extract_text.py` needs only the standard library for `.docx` and `.pages`; `pypdf` is required
only for PDFs.

### Quick start

```bash
# 1. keep real data OUT of the repo
mkdir -p private
cp templates/candidate-profile.example.yaml private/candidate-profile.yaml
cp templates/resume-config.example.yaml    private/resume-config.yaml
cp templates/tracker.example.yaml          private/tracker.yaml

# 2. extract a JD
python scripts/extract_text.py path/to/jd.docx --out private/jds/

# 3. build a tailored resume (with structural checks)
python scripts/build_resume.py private/resume-config.yaml --out private/out/ --verify

# 4. build the tracker
python scripts/build_tracker.py private/tracker.yaml --out private/out/tracker.xlsx

# 5. BEFORE publishing anything, run the gates
python scripts/scan_pii.py . --fail-on-find
python scripts/check_skill.py
```

### Repository layout

```
SKILL.md                    entry point: when to use, the pipeline, the core rules
references/
  01-collect-jds.md         JD sources, text extraction, requirement decomposition
  02-tailor-resume.md       the JD → evidence → bullet method, with worked examples
  03-resume-formatting.md   layout profiles, exact parameters, OOXML traps
  04-find-portals.md        resolving the canonical apply path, ATS recognition
  05-autofill-webforms.md   assisted prefill, guardrails, credential handling
  06-track-applications.md  tracker schema, status vocabulary, operating cadence
  07-interview-prep.md      psychometrics, video interviews, manager interviews
  08-cover-letter.md        cover letters, application emails, open-question answers
scripts/
  extract_text.py           .docx / .pages / .pdf / .html / .txt → text
  build_resume.py           config → .docx, with structural verification
  build_tracker.py          config → .xlsx tracker with dropdowns and colours
  scan_pii.py               personal-data scan before publishing
  check_skill.py            frontmatter, YAML, links, compile checks
templates/                  placeholder-only starting points
examples/
  jd-mirroring-walkthrough.md   a de-identified walkthrough of the tailoring method
  sample-output/                a real generated sample resume (config + docx + pdf)
PUBLISHING.md               repo metadata, release notes, first-push checklist
.github/workflows/ci.yml    PII gate + skill integrity, on every push
docs/release-v1.0.0.md      ready-to-paste GitHub release body
```

### Safety and privacy

- **No auto-submit.** The workflow prefills and hands the submit button back to the human. There is
  deliberately no auto-submit code path.
- **No credential handling.** You sign in yourself; the assistant works in the session you already
  have open. Credentials are never typed, stored, or logged by these scripts.
- **No CAPTCHA / bot-check bypass.** If a check appears, the workflow stops and hands over.
- **Enabled-only data.** Real candidate data lives in a git-ignored `private/` directory. Run
  `scan_pii.py` before every push or share.
- **Platform rules respected.** Where a site's terms disallow automation, only the prepared-answers
  mode is used.

### CI enforces the privacy promise

A skill about handling personal career data must never itself ship personal data, so the promise is
machine-checked rather than merely documented. `.github/workflows/ci.yml` runs on every push and
pull request:

**`pii-guard`** — hard gate, dependency-free so it can never be skipped:

- runs `scan_pii.py . --fail-on-find` over the tracked tree
- fails if any `private/` path, `.docx` / `.pdf` / `.xlsx` / key file is tracked in git
- asserts the de-identified sample is the *only* committed document binary

**`skill-check`** — structural integrity across Python 3.10 and 3.12:

- SKILL.md frontmatter is valid and says when to use the skill
- every template YAML parses
- every relative Markdown link resolves
- every script compiles
- the three builders are smoke-tested end to end

Run both locally before pushing:

```bash
python scripts/scan_pii.py . --fail-on-find
python scripts/check_skill.py
```

### Licence

MIT — see [LICENSE](LICENSE).

---

## 中文说明

一个用于**校招 / 实习求职全流程**的 agent skill：收集 JD、按 JD 逐条改写简历、找到官方投递入口、
辅助填写网申表单（**绝不自动提交**）、维护投递台账、并准备后续的测评与面试。

为**公开发布**而设计，仓库内不含任何个人信息，所有示例与模版一律使用占位符。

### 五个阶段

1. **收集** — 把 JD（`.docx` / `.pages` / `.pdf` / 网页 / 粘贴文本）拆成结构化的要求清单
2. **改写** — 一个 JD 一份简历；把每条要求映射到最强的一条真实经历，用 JD 自己的措辞重写
3. **排版** — 输出两种版式之一（`modern` 大厂风 / `ats` 通用风），保证可被解析、可读
4. **投递** — 定位官方投递入口，并按安全规程辅助预填网申表单
5. **跟踪与准备** — 投递台账 + 测评 / 视频面 / 业务面的结构化准备

### 核心原则

**每条 JD 要求 → 最强的一条真实证据 → 一条用 JD 语言写成的 bullet。**

没有对应证据时，记录为**诚实的空缺**，而不是编造一条经历。编造的 bullet 会变成面试中答不上来的问题——
所以这条诚实规则是结构性的，不是可选项。

### 隐私与安全

- **不自动提交**：预填完成后，提交按钮交还给人，代码中刻意不存在自动提交路径。
- **不接触账号密码**：你自己登录，助手只在你已登录的会话里工作；脚本不会输入、存储或记录凭据。
- **不绕过验证码 / 反爬**：遇到验证即停止并交还控制权。
- **数据隔离**：真实个人信息放在被 git 忽略的 `private/` 目录；每次推送前运行 `scan_pii.py`。

### 许可

MIT。

### 一句话

把「投一百家」从重复劳动变成一条可复用、可验证、且不会编造经历的流水线。
