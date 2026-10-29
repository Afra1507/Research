"""
Module E — Resource (paper / stationery) calculator.

For each scheduled exam, computes item quantities from institutional norms
with waste buffers (Theory 5%, Practical 3% by default), then aggregates a
procurement report (sheets + reams).

Formula per item:
  copies = ceil(enrolled * (1 + buffer_pct/100))
  sheets = copies * sheets_per_student
  reams  = sheets / ream_size
"""

from __future__ import annotations

import csv
import json
import math
import time as time_mod
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from .csp_solver import DEFAULT_DATA, REPO_ROOT, SlotAssignment
    from .hr_allocator import load_schedule_csv
except ImportError:
    from csp_solver import DEFAULT_DATA, REPO_ROOT, SlotAssignment  # type: ignore
    from hr_allocator import load_schedule_csv  # type: ignore


@dataclass(frozen=True)
class StationeryNorm:
    item: str
    exam_type: str
    sheets_per_student: int
    waste_buffer_pct: float
    ream_size: int
    notes: str = ""


@dataclass(frozen=True)
class ExamResourceLine:
    course_code: str
    exam_date: str
    exam_type: str
    enrolled: int
    item: str
    buffer_pct: float
    copies: int
    sheets_per_copy: int
    sheets_total: int
    reams: float


@dataclass
class ResourceCalcResult:
    success: bool
    lines: list[ExamResourceLine] = field(default_factory=list)
    procurement: dict[str, dict[str, float]] = field(default_factory=dict)
    totals: dict[str, float] = field(default_factory=dict)
    baseline_comparison: dict[str, float] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "totals": self.totals,
            "procurement": self.procurement,
            "baseline_comparison": self.baseline_comparison,
            "lines": [asdict(x) for x in self.lines],
        }


def load_stationery_norms(data_dir: Path = DEFAULT_DATA) -> list[StationeryNorm]:
    path = data_dir / "stationery_norms.csv"
    norms: list[StationeryNorm] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            norms.append(
                StationeryNorm(
                    item=row["item"],
                    exam_type=row["exam_type"],
                    sheets_per_student=int(row["sheets_per_student"]),
                    waste_buffer_pct=float(row["waste_buffer_pct"]),
                    ream_size=int(row["ream_size"]),
                    notes=row.get("notes") or "",
                )
            )
    return norms


def _copies_with_buffer(enrolled: int, buffer_pct: float) -> int:
    return max(0, math.ceil(enrolled * (1.0 + buffer_pct / 100.0)))


def _naive_baseline_copies(enrolled: int) -> int:
    """Crude manual practice: round enrolled up to next 10, then +10%."""
    if enrolled <= 0:
        return 0
    rounded = int(math.ceil(enrolled / 10.0) * 10)
    return int(math.ceil(rounded * 1.10))


def calculate_resources(
    schedule: list[SlotAssignment],
    norms: list[StationeryNorm],
) -> ResourceCalcResult:
    t0 = time_mod.perf_counter()
    by_type: dict[str, list[StationeryNorm]] = defaultdict(list)
    for n in norms:
        by_type[n.exam_type].append(n)

    lines: list[ExamResourceLine] = []
    precise_sheets = 0
    baseline_sheets = 0

    for exam in sorted(schedule, key=lambda a: (a.exam_date, a.course_code)):
        applicable = by_type.get(exam.exam_type, [])
        if not applicable:
            continue
        for norm in applicable:
            copies = _copies_with_buffer(exam.enrolled, norm.waste_buffer_pct)
            sheets = copies * norm.sheets_per_student
            reams = sheets / norm.ream_size if norm.ream_size else 0.0
            lines.append(
                ExamResourceLine(
                    course_code=exam.course_code,
                    exam_date=exam.exam_date,
                    exam_type=exam.exam_type,
                    enrolled=exam.enrolled,
                    item=norm.item,
                    buffer_pct=norm.waste_buffer_pct,
                    copies=copies,
                    sheets_per_copy=norm.sheets_per_student,
                    sheets_total=sheets,
                    reams=round(reams, 4),
                )
            )
            precise_sheets += sheets

            base_copies = _naive_baseline_copies(exam.enrolled)
            baseline_sheets += base_copies * norm.sheets_per_student

    # Aggregate procurement by item
    procurement: dict[str, dict[str, float]] = {}
    for line in lines:
        bucket = procurement.setdefault(
            line.item,
            {"copies": 0, "sheets_total": 0, "reams": 0.0},
        )
        bucket["copies"] += line.copies
        bucket["sheets_total"] += line.sheets_total
        # recompute reams from sheets using 500 default if mixed — use line reams sum
        bucket["reams"] += line.reams

    for item, bucket in procurement.items():
        bucket["copies"] = int(bucket["copies"])
        bucket["sheets_total"] = int(bucket["sheets_total"])
        bucket["reams"] = round(bucket["reams"], 4)

    total_reams = round(sum(v["reams"] for v in procurement.values()), 4)
    reduction_pct = (
        round(100.0 * (baseline_sheets - precise_sheets) / baseline_sheets, 2)
        if baseline_sheets > 0
        else 0.0
    )

    totals = {
        "exams": len(schedule),
        "line_items": len(lines),
        "sheets_total": precise_sheets,
        "reams_total": total_reams,
    }
    baseline_comparison = {
        "baseline_sheets_total": baseline_sheets,
        "precise_sheets_total": precise_sheets,
        "sheets_saved": baseline_sheets - precise_sheets,
        "reduction_pct_vs_naive": reduction_pct,
    }

    return ResourceCalcResult(
        success=True,
        lines=lines,
        procurement=procurement,
        totals=totals,
        baseline_comparison=baseline_comparison,
        elapsed_seconds=time_mod.perf_counter() - t0,
        message=(
            f"Computed {len(lines)} resource lines for {len(schedule)} exams; "
            f"{precise_sheets} sheets ({total_reams} reams); "
            f"{reduction_pct}% below naive baseline"
        ),
    )


def run_resource_calculator(
    data_dir: Path | str = DEFAULT_DATA,
    *,
    schedule: Optional[list[SlotAssignment]] = None,
    prefer_ga: bool = True,
) -> ResourceCalcResult:
    data_dir = Path(data_dir)
    if schedule is None:
        ga_path = data_dir / "output" / "schedule_ga.csv"
        csp_path = data_dir / "output" / "schedule.csv"
        if prefer_ga and ga_path.exists():
            schedule = load_schedule_csv(ga_path)
        elif csp_path.exists():
            schedule = load_schedule_csv(csp_path)
        else:
            raise FileNotFoundError("No schedule.csv / schedule_ga.csv found; run CSP/GA first")

    norms = load_stationery_norms(data_dir)
    return calculate_resources(schedule, norms)


def export_resource_result(result: ResourceCalcResult, out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    detail = out_dir / "exam_resources.csv"
    fields = [
        "course_code",
        "exam_date",
        "exam_type",
        "enrolled",
        "item",
        "buffer_pct",
        "copies",
        "sheets_per_copy",
        "sheets_total",
        "reams",
    ]
    with detail.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for line in result.lines:
            writer.writerow(asdict(line))

    proc = out_dir / "procurement_report.csv"
    with proc.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item", "copies", "sheets_total", "reams"])
        writer.writeheader()
        for item, bucket in sorted(result.procurement.items()):
            writer.writerow({"item": item, **bucket})

    with (out_dir / "resource_summary.json").open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    with (out_dir / "resource_report.txt").open("w", encoding="utf-8") as f:
        f.write(result.message + "\n")
        f.write(f"success={result.success}\n")
        f.write(f"totals={result.totals}\n")
        f.write(f"baseline_comparison={result.baseline_comparison}\n")
        f.write("\nProcurement by item:\n")
        for item, bucket in sorted(result.procurement.items()):
            f.write(
                f"  {item}: copies={bucket['copies']}, "
                f"sheets={bucket['sheets_total']}, reams={bucket['reams']}\n"
            )
    return detail


if __name__ == "__main__":
    result = run_resource_calculator()
    out = REPO_ROOT / "data" / "tier3" / "output"
    export_resource_result(result, out)
    print(result.message)
    print("totals:", result.totals)
    print("vs baseline:", result.baseline_comparison)
