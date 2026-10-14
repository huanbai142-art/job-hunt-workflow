#!/usr/bin/env python3
"""Build an application tracker workbook (.xlsx) from a YAML or CSV source.

Features:
  * frozen + filtered header row
  * a dropdown validator on `status` bound to a closed vocabulary
  * colour fills per status
  * deadline highlighting for imminent / overdue dates

Usage:
    pip install openpyxl pyyaml
    python build_tracker.py tracker.yaml --out ./out/tracker.xlsx
    python build_tracker.py tracker.csv  --out ./out/tracker.xlsx
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
except ImportError:
    raise SystemExit("This script needs openpyxl:  pip install openpyxl")

try:
    import yaml
except ImportError:
    raise SystemExit("This script needs PyYAML:  pip install pyyaml")

# Closed status vocabulary -> row colour
STATUS_COLORS = {
    "待投":    "F2F2F2",
    "已投":    "DDEBF7",
    "测评中":  "FFF2CC",
    "测评完成": "E2EFDA",
    "面试中":  "FCE4D6",
    "Offer":   "C6EFCE",
    "已拒":    "F8CBAD",
    "无回应":  "D9D9D9",
}

COLUMNS = [
    ("company", "公司", 20),
    ("role", "岗位", 26),
    ("resume_version", "简历版本", 24),
    ("status", "状态", 12),
    ("channel", "投递渠道", 18),
    ("deadline", "截止时间", 14),
    ("applied_on", "投递日期", 14),
    ("next_action_on", "下一步日期", 14),
    ("next_action", "下一步动作", 24),
    ("link", "链接", 34),
    ("notes", "备注", 30),
]


def as_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return dt.datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("applications", [])
    return data or []


def build(rows: list[dict], out: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "投递台账"

    # header
    for col, (_, label, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width

    # rows
    for r, row in enumerate(rows, start=2):
        for c, (key, _, _) in enumerate(COLUMNS, start=1):
            value = row.get(key, "")
            if key in {"deadline", "applied_on", "next_action_on"}:
                value = as_date(value)
                if value:
                    ws.cell(row=r, column=c).number_format = "YYYY-MM-DD"
            ws.cell(row=r, column=c, value=value)
            ws.cell(row=r, column=c).alignment = Alignment(
                vertical="top", wrap_text=(key in {"notes", "next_action"})
            )

        status = row.get("status")
        if status in STATUS_COLORS:
            fill = PatternFill("solid", fgColor=STATUS_COLORS[status])
            for c in range(1, len(COLUMNS) + 1):
                ws.cell(row=r, column=c).fill = fill

    last = max(len(rows) + 1, 2)

    # status dropdown
    status_col = [k for k, _, _ in COLUMNS].index("status") + 1
    letter = get_column_letter(status_col)
    dv = DataValidation(
        type="list",
        formula1='"' + ",".join(STATUS_COLORS) + '"',
        allow_blank=True,
        showDropDown=False,
    )
    dv.error = "请从下拉列表中选择状态"
    dv.errorTitle = "无效状态"
    ws.add_data_validation(dv)
    dv.add(f"{letter}2:{letter}{last + 200}")

    # deadline highlighting
    dl_col = [k for k, _, _ in COLUMNS].index("deadline") + 1
    dl_letter = get_column_letter(dl_col)
    rng = f"{dl_letter}2:{dl_letter}{last + 200}"
    today = dt.date.today()
    ws.conditional_formatting.add(
        rng,
        CellIsRule(operator="lessThan",
                   formula=[f'"{today.isoformat()}"'],
                   fill=PatternFill("solid", fgColor="FFC7CE"),
                   font=Font(color="9C0006")),
    )
    ws.conditional_formatting.add(
        rng,
        CellIsRule(operator="between",
                   formula=[f'"{today.isoformat()}"',
                            f'"{(today + dt.timedelta(days=7)).isoformat()}"'],
                   fill=PatternFill("solid", fgColor="FFEB9C"),
                   font=Font(color="9C6500")),
    )

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{last}"

    # roll-up sheet
    summary = wb.create_sheet("汇总")
    summary.append(["状态", "数量"])
    counts: dict[str, int] = {k: 0 for k in STATUS_COLORS}
    for row in rows:
        s = row.get("status")
        if s in counts:
            counts[s] += 1
    for k, v in counts.items():
        summary.append([k, v])
    summary["A1"].font = Font(bold=True)
    summary["B1"].font = Font(bold=True)
    summary.column_dimensions["A"].width = 16
    summary.column_dimensions["B"].width = 10

    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="YAML or CSV of applications")
    ap.add_argument("--out", default="./out/tracker.xlsx")
    args = ap.parse_args()

    rows = load_rows(Path(args.source))
    out = build(rows, Path(args.out))
    print(f"[built] {out}  ({len(rows)} applications)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
