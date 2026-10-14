#!/usr/bin/env python3
"""Validate the skill's own integrity.

Checks, all offline and dependency-light:

  1. SKILL.md has YAML frontmatter with a `name` and a `description`, and the
     description states when the skill should be used.
  2. Every template YAML parses (skipped with a warning if PyYAML is absent).
  3. Every relative Markdown link in the repository resolves to an existing file.
  4. Every script under scripts/ compiles.

Run locally or in CI:

    python scripts/check_skill.py            # check the repo containing this file
    python scripts/check_skill.py --root .   # explicit root

Exit code 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import py_compile
import re
import sys
import tempfile
from pathlib import Path

FAILURES: list[str] = []
WARNINGS: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)


def warn(msg: str) -> None:
    WARNINGS.append(msg)


# --------------------------------------------------------------------------- #
# 1. frontmatter
# --------------------------------------------------------------------------- #
def check_frontmatter(root: Path) -> None:
    skill = root / "SKILL.md"
    if not skill.exists():
        fail("SKILL.md is missing")
        return

    text = skill.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        fail("SKILL.md has no YAML frontmatter block")
        return

    block = m.group(1)
    fields: dict[str, str] = {}
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(block) or {}
        fields = {k: str(v) for k, v in loaded.items()}
    except ImportError:
        warn("PyYAML not installed; using a plain-text frontmatter parse")
        for line in block.splitlines():
            if ": " in line and not line.startswith((" ", "\t", "-")):
                key, value = line.split(": ", 1)
                fields[key.strip()] = value.strip()

    for required in ("name", "description"):
        if not fields.get(required):
            fail(f"SKILL.md frontmatter is missing `{required}`")

    description = fields.get("description", "")
    if description and "use when" not in description.lower():
        warn("SKILL.md `description` does not say when to use the skill; "
             "discovery depends on it")

    if len(description) > 1024:
        warn(f"SKILL.md `description` is {len(description)} chars; long "
             "descriptions can be truncated by some runtimes")

    print(f"[ok]  SKILL.md frontmatter (name={fields.get('name')!r})")


# --------------------------------------------------------------------------- #
# 2. templates parse
# --------------------------------------------------------------------------- #
def check_templates(root: Path) -> None:
    templates = sorted((root / "templates").glob("*.yaml"))
    if not templates:
        warn("no template YAML files found under templates/")
        return

    try:
        import yaml  # type: ignore
    except ImportError:
        warn(f"PyYAML not installed; skipped parsing {len(templates)} template(s)")
        return

    for path in templates:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fail(f"{path.relative_to(root)} is not valid YAML: {exc}")

    example_dir = root / "examples" / "sample-output"
    for path in sorted(example_dir.glob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            fail(f"{path.relative_to(root)} is not valid YAML: {exc}")

    print(f"[ok]  {len(templates)} template(s) parse as YAML")


# --------------------------------------------------------------------------- #
# 3. internal links
# --------------------------------------------------------------------------- #
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def check_links(root: Path) -> None:
    checked = 0
    for md in sorted(root.rglob("*.md")):
        if any(part.startswith(".") and part != "." for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8")
        for label, target in LINK.findall(text):
            clean = target.split("#")[0].strip()
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if not (md.parent / clean).exists():
                fail(f"{md.relative_to(root)}: broken link "
                     f"[{label}]({target})")
            checked += 1
    print(f"[ok]  {checked} internal link(s) resolve")


# --------------------------------------------------------------------------- #
# 4. scripts compile
# --------------------------------------------------------------------------- #
def check_scripts(root: Path) -> None:
    scripts = sorted((root / "scripts").glob("*.py"))
    if not scripts:
        warn("no scripts found under scripts/")
        return

    with tempfile.TemporaryDirectory() as tmp:
        for path in scripts:
            try:
                py_compile.compile(
                    str(path),
                    cfile=str(Path(tmp) / (path.stem + ".pyc")),
                    doraise=True,
                )
            except py_compile.PyCompileError as exc:
                fail(f"{path.relative_to(root)} does not compile: {exc}")

    print(f"[ok]  {len(scripts)} script(s) compile")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None,
                    help="repository root (default: the parent of this script)")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    print(f"checking skill at {root}\n")

    check_frontmatter(root)
    check_templates(root)
    check_links(root)
    check_scripts(root)

    print()
    for w in WARNINGS:
        print(f"[warn] {w}")
    for f in FAILURES:
        print(f"[FAIL] {f}")

    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} failure(s).")
        return 1
    print("RESULT: skill integrity OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
