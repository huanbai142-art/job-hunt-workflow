#!/usr/bin/env python3
"""Scan a path for personal information before publishing or sharing.

Flags common personal-data patterns so nothing leaks into a public repository:
emails, phone numbers, national ID numbers, bank cards, URLs with credentials,
and files that look like real resumes or profiles.

This is a *heuristic* gate, not a guarantee. It reduces the chance of an
accidental leak; it does not prove absence.

Usage:
    python scan_pii.py .                 # scan the current directory
    python scan_pii.py . --quiet         # only print findings
    python scan_pii.py . --fail-on-find  # exit 1 when anything is found (for CI)

Exit codes:
    0  clean (or findings present without --fail-on-find)
    1  findings present and --fail-on-find was given
    2  usage error
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Files we never scan for content (binary / vendored)
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
               ".docx", ".xlsx", ".zip", ".woff", ".woff2", ".ttf", ".otf"}

# Filenames that should never be published.
# A `.example.` / `.template.` infix marks a deliberate template, and this skill's own
# docs and scripts legitimately contain these words, so those are not flagged — only
# real *instances* such as `my-resume-final.pdf` are.
RISKY_FILENAMES = re.compile(
    r"(resume|cv|简历|profile|application|投递|台账|transcript|成绩单|护照|passport)",
    re.IGNORECASE,
)
TEMPLATE_HINT = re.compile(r"(\.example\.|\.template\.)", re.IGNORECASE)
# This skill's own documentation and scripts legitimately contain words like
# "resume" and "profile" in their filenames, so files that live inside the skill
# directory are exempt from the filename check. Everything else is not.
SKILL_ROOT_MARKER = "job-hunt-workflow"

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email",
     re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("cn_mobile",
     re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("cn_id_card",
     re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("cn_bank_card",
     re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
    ("phone_intl",
     re.compile(r"\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}")),
    ("hk_mo_tw_id",
     re.compile(r"(?<![A-Za-z0-9])[A-Z]{1,2}\d{6}\(?[0-9A]\)?")),
    ("url_with_credentials",
     re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")),
    ("private_key",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password_assignment",
     re.compile(r"(password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*[^\s\"'{<]",
                re.IGNORECASE)),
]

# Placeholders are expected and fine
ALLOWLIST = re.compile(
    r"(\{\{[A-Z_]+\}\}|example\.com|you@example|user@example|<[^>]+>|"
    r"xxx+|\bTODO\b|placeholder)",
    re.IGNORECASE,
)


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIX:
        return False
    try:
        with path.open("rb") as fh:
            chunk = fh.read(4096)
        return b"\x00" not in chunk
    except OSError:
        return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings

    for lineno, line in enumerate(text.splitlines(), start=1):
        if ALLOWLIST.search(line):
            continue
        for label, pattern in PATTERNS:
            for m in pattern.finditer(line):
                snippet = m.group(0)
                if len(snippet) > 60:
                    snippet = snippet[:57] + "..."
                findings.append((lineno, label, snippet))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".", help="file or directory to scan")
    ap.add_argument("--quiet", action="store_true", help="only print findings")
    ap.add_argument("--fail-on-find", action="store_true",
                    help="exit non-zero when anything is found")
    args = ap.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else [
        p for p in root.rglob("*")
        if p.is_file()
        and not any(part in SKIP_DIRS for part in p.parts)
    ]

    total = 0
    risky_names: list[Path] = []

    for path in sorted(files):
        inside_skill = SKILL_ROOT_MARKER in str(path.resolve())
        if (RISKY_FILENAMES.search(path.name)
                and not TEMPLATE_HINT.search(path.name)
                and not inside_skill):
            risky_names.append(path)

        if not is_probably_text(path):
            continue

        findings = scan_file(path)
        if findings:
            rel = path.relative_to(root) if root.is_dir() else path.name
            for lineno, label, snippet in findings:
                print(f"{rel}:{lineno}: [{label}] {snippet}")
                total += 1

    if risky_names:
        print("\nFiles whose *names* suggest personal data "
              "(confirm they are git-ignored):")
        for p in risky_names:
            rel = p.relative_to(root) if root.is_dir() else p.name
            print(f"  - {rel}")
        total += len(risky_names)

    if not args.quiet:
        print()
        if total:
            print(f"RESULT: {total} potential issue(s) found. Review each one.")
            print("Reminder: placeholders like {{FULL_NAME}} are expected and safe.")
        else:
            print("RESULT: no obvious personal data found.")
            print("Reminder: this is a heuristic check, not a guarantee.")

    if total and args.fail_on_find:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
