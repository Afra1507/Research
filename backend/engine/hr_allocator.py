"""
Module D — Human resource (invigilation) allocator.

Assigns Chief Supervisor, Invigilators, Hall Attendants, and Technical Officers
to each scheduled exam using proposal ratios, while respecting hard constraints:

  - No staff on two overlapping exams
  - Course lecturer cannot be assigned to their own exam
  - At least one rest session between consecutive duties on the same day
  - Role eligibility flags and max_duties_per_period

Theory ratios:
  1 Chief Supervisor, 1 Invigilator / 30 students, 1 Hall Attendant / 60 students

Practical ratios:
  1 Chief Supervisor, 1 Invigilator / 15 students, 1 Technical Officer,
  1 Hall Attendant / 40 students
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import time as time_mod
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Optional

try:
    from .csp_solver import (
        DEFAULT_DATA,
        REPO_ROOT,
        SlotAssignment,
        _overlaps,
        _parse_hhmm,
        run_csp,
    )
    from .ga_optimiser import run_ga
except ImportError:  # running as a script
    from csp_solver import (  # type: ignore
        DEFAULT_DATA,
        REPO_ROOT,
        SlotAssignment,
        _overlaps,
        _parse_hhmm,
        run_csp,
    )
    from ga_optimiser import run_ga  # type: ignore

SESSION_ORDER = ("08:00", "10:00", "13:00", "15:30")
SESSION_INDEX = {s: i for i, s in enumerate(SESSION_ORDER)}


@dataclass
class StaffMember:
    staff_id: str
    display_name: str
    designation: str
    can_be_chief_supervisor: bool
    can_be_invigilator: bool
    can_be_hall_attendant: bool
    can_be_technical_officer: bool
    max_duties_per_period: int
    teaches_course_codes: set[str]


@dataclass(frozen=True)
class DutyAssignment:
    course_code: str
    exam_date: str
    start_time: str
    end_time: str
    room_id: str
    exam_type: str
    enrolled: int
    staff_id: str
    staff_name: str
    duty_role: str  # ChiefSupervisor | Invigilator | HallAttendant | TechnicalOfficer


@dataclass
class RoleRequirement:
    chief_supervisors: int
    invigilators: int
    hall_attendants: int
    technical_officers: int

    def total(self) -> int:
        return (
            self.chief_supervisors
            + self.invigilators
            + self.hall_attendants
            + self.technical_officers
        )


@dataclass
class HRAllocationResult:
    success: bool
    duties: list[DutyAssignment] = field(default_factory=list)
    unfilled: list[str] = field(default_factory=list)
    duty_counts: dict[str, int] = field(default_factory=dict)
    duty_balance_std: float = 0.0
    elapsed_seconds: float = 0.0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "unfilled": self.unfilled,
            "duty_balance_std": self.duty_balance_std,
            "duty_counts": self.duty_counts,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "duties": [asdict(d) for d in self.duties],
        }


def required_roles(exam_type: str, enrolled: int) -> RoleRequirement:
    n = max(0, int(enrolled))
    if exam_type == "Practical":
        return RoleRequirement(
            chief_supervisors=1,
            invigilators=max(1, math.ceil(n / 15)),
            hall_attendants=max(1, math.ceil(n / 40)),
            technical_officers=1,
        )
    return RoleRequirement(
        chief_supervisors=1,
        invigilators=max(1, math.ceil(n / 30)),
        hall_attendants=max(1, math.ceil(n / 60)),
        technical_officers=0,
    )


def load_staff(data_dir: Path = DEFAULT_DATA) -> list[StaffMember]:
    path = data_dir / "staff.csv"
    staff: list[StaffMember] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            taught = {
                c.strip()
                for c in (row.get("teaches_course_codes") or "").split(";")
                if c.strip()
            }
            staff.append(
                StaffMember(
                    staff_id=row["staff_id"],
                    display_name=row.get("display_name") or row["staff_id"],
                    designation=row["designation"],
                    can_be_chief_supervisor=row["can_be_chief_supervisor"] == "Y",
                    can_be_invigilator=row["can_be_invigilator"] == "Y",
                    can_be_hall_attendant=row["can_be_hall_attendant"] == "Y",
                    can_be_technical_officer=row["can_be_technical_officer"] == "Y",
                    max_duties_per_period=int(row.get("max_duties_per_period") or 4),
                    teaches_course_codes=taught,
                )
            )
    return staff


def load_schedule_csv(path: Path) -> list[SlotAssignment]:
    assignments: list[SlotAssignment] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            assignments.append(
                SlotAssignment(
                    course_code=row["course_code"],
                    exam_date=row["exam_date"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    room_id=row["room_id"],
                    exam_type=row["exam_type"],
                    enrolled=int(row["enrolled"]),
                    year_level=int(row["year_level"]),
                    lecturer_staff_id=row.get("lecturer_staff_id") or None,
                )
            )
    return assignments


def _session_index(start_time: str) -> int:
    if start_time in SESSION_INDEX:
        return SESSION_INDEX[start_time]
    # nearest known session
    t = _parse_hhmm(start_time)
    best = min(
        SESSION_ORDER,
        key=lambda s: abs(
            datetime.combine(date.today(), _parse_hhmm(s))
            - datetime.combine(date.today(), t)
        ).total_seconds(),
    )
    return SESSION_INDEX[best]


def _has_rest_session(existing: list[DutyAssignment], candidate: SlotAssignment) -> bool:
    """True if candidate respects one-rest-session rule vs existing duties."""
    c_start = _parse_hhmm(candidate.start_time)
    c_end = _parse_hhmm(candidate.end_time)
    c_idx = _session_index(candidate.start_time)
    for d in existing:
        if d.exam_date != candidate.exam_date:
            continue
        d_start = _parse_hhmm(d.start_time)
        d_end = _parse_hhmm(d.end_time)
        if _overlaps(c_start, c_end, d_start, d_end):
            return False
        d_idx = _session_index(d.start_time)
        if abs(c_idx - d_idx) < 2:
            # adjacent sessions (e.g. 08:00 then 10:00) — no rest session between
            return False
    return True


def _eligible(
    staff: StaffMember,
    role: str,
    exam: SlotAssignment,
    duty_counts: dict[str, int],
    duties_by_staff: dict[str, list[DutyAssignment]],
) -> bool:
    if exam.lecturer_staff_id and staff.staff_id == exam.lecturer_staff_id:
        return False
    if exam.course_code in staff.teaches_course_codes:
        return False
    if duty_counts.get(staff.staff_id, 0) >= staff.max_duties_per_period:
        return False
    if role == "ChiefSupervisor" and not staff.can_be_chief_supervisor:
        return False
    if role == "Invigilator" and not staff.can_be_invigilator:
        return False
    if role == "HallAttendant" and not staff.can_be_hall_attendant:
        return False
    if role == "TechnicalOfficer" and not staff.can_be_technical_officer:
        return False
    if not _has_rest_session(duties_by_staff.get(staff.staff_id, []), exam):
        return False
    return True


def allocate_staff(
    schedule: list[SlotAssignment],
    staff: list[StaffMember],
) -> HRAllocationResult:
    t0 = time_mod.perf_counter()
    duties: list[DutyAssignment] = []
    unfilled: list[str] = []
    duty_counts: dict[str, int] = defaultdict(int)
    duties_by_staff: dict[str, list[DutyAssignment]] = defaultdict(list)

    # Process denser / earlier exams first
    ordered = sorted(schedule, key=lambda a: (a.exam_date, a.start_time, -a.enrolled))

    role_plan: list[tuple[str, int]] = []

    for exam in ordered:
        req = required_roles(exam.exam_type, exam.enrolled)
        role_plan = (
            [("ChiefSupervisor", req.chief_supervisors)]
            + [("Invigilator", req.invigilators)]
            + [("TechnicalOfficer", req.technical_officers)]
            + [("HallAttendant", req.hall_attendants)]
        )
        assigned_ids: set[str] = set()

        for role, count in role_plan:
            for _ in range(count):
                candidates = [
                    s
                    for s in staff
                    if s.staff_id not in assigned_ids
                    and _eligible(s, role, exam, duty_counts, duties_by_staff)
                ]
                # Prefer fewer current duties (balance), then staff_id for stability
                candidates.sort(key=lambda s: (duty_counts[s.staff_id], s.staff_id))
                if not candidates:
                    unfilled.append(
                        f"{exam.course_code} {exam.exam_date} {exam.start_time}: "
                        f"need {role}"
                    )
                    continue
                pick = candidates[0]
                duty = DutyAssignment(
                    course_code=exam.course_code,
                    exam_date=exam.exam_date,
                    start_time=exam.start_time,
                    end_time=exam.end_time,
                    room_id=exam.room_id,
                    exam_type=exam.exam_type,
                    enrolled=exam.enrolled,
                    staff_id=pick.staff_id,
                    staff_name=pick.display_name,
                    duty_role=role,
                )
                duties.append(duty)
                assigned_ids.add(pick.staff_id)
                duty_counts[pick.staff_id] += 1
                duties_by_staff[pick.staff_id].append(duty)

    counts_list = list(duty_counts.values()) if duty_counts else [0]
    # Include staff with zero duties for a fairer balance index over eligible pool
    for s in staff:
        duty_counts.setdefault(s.staff_id, 0)
    active_counts = [c for c in duty_counts.values() if c > 0]
    balance_std = (
        statistics.pstdev(active_counts) if len(active_counts) >= 2 else 0.0
    )

    success = len(unfilled) == 0
    return HRAllocationResult(
        success=success,
        duties=sorted(
            duties,
            key=lambda d: (d.exam_date, d.start_time, d.course_code, d.duty_role, d.staff_id),
        ),
        unfilled=unfilled,
        duty_counts=dict(sorted(duty_counts.items())),
        duty_balance_std=balance_std,
        elapsed_seconds=time_mod.perf_counter() - t0,
        message=(
            f"Assigned {len(duties)} duties across {len(active_counts)} staff; "
            f"balance_std={balance_std:.3f}"
            + ("" if success else f"; unfilled={len(unfilled)}")
        ),
    )


def run_hr_allocator(
    data_dir: Path | str = DEFAULT_DATA,
    *,
    schedule: Optional[list[SlotAssignment]] = None,
    prefer_ga: bool = True,
) -> HRAllocationResult:
    data_dir = Path(data_dir)
    if schedule is None:
        ga_path = data_dir / "output" / "schedule_ga.csv"
        csp_path = data_dir / "output" / "schedule.csv"
        if prefer_ga and ga_path.exists():
            schedule = load_schedule_csv(ga_path)
        elif csp_path.exists():
            schedule = load_schedule_csv(csp_path)
        else:
            ga = run_ga(data_dir, n_runs=3, generations=20, population_size=20)
            schedule = ga.assignments if ga.success else run_csp(data_dir).assignments

    staff = load_staff(data_dir)
    return allocate_staff(schedule, staff)


def export_hr_result(result: HRAllocationResult, out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "staff_duties.csv"
    fields = [
        "course_code",
        "exam_date",
        "start_time",
        "end_time",
        "room_id",
        "exam_type",
        "enrolled",
        "staff_id",
        "staff_name",
        "duty_role",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for d in result.duties:
            writer.writerow(asdict(d))

    with (out_dir / "hr_summary.json").open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    with (out_dir / "hr_report.txt").open("w", encoding="utf-8") as f:
        f.write(result.message + "\n")
        f.write(f"success={result.success}\n")
        f.write(f"duties={len(result.duties)}\n")
        f.write(f"duty_balance_std={result.duty_balance_std:.4f}\n")
        f.write(f"unfilled={len(result.unfilled)}\n")
        for u in result.unfilled:
            f.write(f"- {u}\n")
        f.write("\nDuties per staff (non-zero):\n")
        for sid, n in sorted(result.duty_counts.items(), key=lambda x: (-x[1], x[0])):
            if n:
                f.write(f"  {sid}: {n}\n")
    return csv_path


if __name__ == "__main__":
    try:
        result = run_hr_allocator()
    except ImportError:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from engine.hr_allocator import export_hr_result, run_hr_allocator  # type: ignore

        result = run_hr_allocator()
    out = REPO_ROOT / "data" / "tier3" / "output"
    export_hr_result(result, out)
    print(result.message)
    print(f"success={result.success} duties={len(result.duties)} std={result.duty_balance_std:.3f}")
    if result.unfilled:
        for u in result.unfilled[:10]:
            print(" ", u)
