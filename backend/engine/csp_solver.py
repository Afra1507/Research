"""
Module B — CSP examination scheduling engine.

Assigns each course an (exam_date, start_time, room) satisfying hard constraints:
  1. Year → fixed session time (config)
  2. No two courses sharing students in overlapping time
  3. Room type match (Theory→ExamHall/LectureHall; Practical→ComputerLab/ScienceLab)
  4. Room capacity >= enrolled students
  5. No lecturer with two overlapping exams
  6. No two exams in the same room at overlapping times

Uses backtracking with MRV (most constrained variable) and forward checking.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, time
from pathlib import Path
from typing import Any, Iterable, Optional

from .parser import load_config, parse_course

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = REPO_ROOT / "data" / "tier3"

THEORY_ROOM_TYPES = frozenset({"ExamHall", "LectureHall"})
PRACTICAL_ROOM_TYPES = frozenset({"ComputerLab", "ScienceLab"})


@dataclass
class CourseExam:
    course_code: str
    course_name: str
    year_level: int
    exam_type: str
    credits: float
    duration_hours: float
    session_time: str
    lecturer_staff_id: Optional[str]
    enrolled: int


@dataclass
class Room:
    room_id: str
    capacity: int
    room_type: str


@dataclass(frozen=True)
class SlotAssignment:
    course_code: str
    exam_date: str  # ISO
    start_time: str  # HH:MM
    end_time: str
    room_id: str
    exam_type: str
    enrolled: int
    year_level: int
    lecturer_staff_id: Optional[str]


@dataclass
class ScheduleResult:
    success: bool
    assignments: list[SlotAssignment] = field(default_factory=list)
    hard_conflicts: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    courses_scheduled: int = 0
    courses_total: int = 0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "courses_scheduled": self.courses_scheduled,
            "courses_total": self.courses_total,
            "hard_conflicts": self.hard_conflicts,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "message": self.message,
            "assignments": [asdict(a) for a in self.assignments],
        }


def _parse_hhmm(value: str) -> time:
    return datetime.strptime(value.strip(), "%H:%M").time()


def _add_hours(start: time, hours: float) -> time:
    base = datetime.combine(date.today(), start)
    return (base + timedelta(hours=hours)).time()


def _overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    """Half-open intervals [start, end) — abutting times do not overlap."""
    return start_a < end_b and start_b < end_a


def working_dates(start: date, end: date) -> list[date]:
    days: list[date] = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # Mon–Fri
            days.append(cur)
        cur += timedelta(days=1)
    return days


def load_tier3(data_dir: Path = DEFAULT_DATA) -> tuple[
    list[CourseExam],
    list[Room],
    dict[str, set[str]],
    date,
    date,
]:
    with (data_dir / "courses.csv").open(encoding="utf-8") as f:
        courses_rows = list(csv.DictReader(f))
    with (data_dir / "enrolment_counts.csv").open(encoding="utf-8") as f:
        counts = {r["course_code"]: int(r["registered_count"]) for r in csv.DictReader(f)}
    with (data_dir / "rooms.csv").open(encoding="utf-8") as f:
        rooms = [
            Room(
                room_id=r["room_id"],
                capacity=int(r["capacity"]),
                room_type=r["room_type"],
            )
            for r in csv.DictReader(f)
            if r.get("exam_usable", "Y") == "Y"
        ]

    with (data_dir / "enrolments.csv").open(encoding="utf-8") as f:
        enrolments = list(csv.DictReader(f))
    students_by_course: dict[str, set[str]] = defaultdict(set)
    for e in enrolments:
        students_by_course[e["course_code"]].add(e["anon_student_id"])

    # conflict neighbours: courses sharing >=1 student
    conflict_graph: dict[str, set[str]] = defaultdict(set)
    codes = list(students_by_course.keys())
    for i, a in enumerate(codes):
        for b in codes[i + 1 :]:
            if students_by_course[a] & students_by_course[b]:
                conflict_graph[a].add(b)
                conflict_graph[b].add(a)

    cfg = load_config()
    exams: list[CourseExam] = []
    for row in courses_rows:
        parsed = parse_course(
            course_code=row["course_code"],
            credits=row["credits"],
            course_name=row["course_name"],
            exam_type=row["exam_type"],
            config=cfg,
        )
        exams.append(
            CourseExam(
                course_code=parsed.course_code,
                course_name=row["course_name"],
                year_level=parsed.year_level,
                exam_type=parsed.exam_type,
                credits=parsed.credits,
                duration_hours=parsed.duration_hours,
                session_time=parsed.session_time,
                lecturer_staff_id=row.get("lecturer_staff_id") or None,
                enrolled=counts.get(parsed.course_code, 0),
            )
        )

    with (data_dir / "exam_calendar.csv").open(encoding="utf-8") as f:
        cal = next(csv.DictReader(f))
    start = date.fromisoformat(cal["exam_start_date"])
    end = date.fromisoformat(cal["exam_end_date"])
    return exams, rooms, conflict_graph, start, end


def _compatible_rooms(exam: CourseExam, rooms: Iterable[Room]) -> list[Room]:
    allowed = (
        PRACTICAL_ROOM_TYPES if exam.exam_type == "Practical" else THEORY_ROOM_TYPES
    )
    fit = [
        r
        for r in rooms
        if r.room_type in allowed and r.capacity >= exam.enrolled
    ]
    # Prefer tighter fit (less waste)
    return sorted(fit, key=lambda r: (r.capacity, r.room_id))


def _violates_hard(
    exam: CourseExam,
    day: date,
    room: Room,
    assignment_map: dict[str, SlotAssignment],
    conflict_graph: dict[str, set[str]],
) -> Optional[str]:
    start = _parse_hhmm(exam.session_time)
    end = _add_hours(start, exam.duration_hours)
    day_s = day.isoformat()

    for other_code, other in assignment_map.items():
        if other.exam_date != day_s:
            continue
        o_start = _parse_hhmm(other.start_time)
        o_end = _parse_hhmm(other.end_time)
        if not _overlaps(start, end, o_start, o_end):
            continue

        if other.room_id == room.room_id:
            return f"Room {room.room_id} double-booked with {other_code}"

        if other_code in conflict_graph.get(exam.course_code, ()):
            return f"Student conflict with {other_code} on {day_s}"

        if (
            exam.lecturer_staff_id
            and other.lecturer_staff_id
            and exam.lecturer_staff_id == other.lecturer_staff_id
        ):
            return f"Lecturer {exam.lecturer_staff_id} overlap with {other_code}"

    return None


class CSPScheduler:
    def __init__(
        self,
        exams: list[CourseExam],
        rooms: list[Room],
        conflict_graph: dict[str, set[str]],
        exam_dates: list[date],
    ) -> None:
        self.exams = {e.course_code: e for e in exams}
        self.rooms = rooms
        self.conflict_graph = conflict_graph
        self.exam_dates = exam_dates
        self.domains: dict[str, list[tuple[date, Room]]] = {}
        for e in exams:
            options = [
                (d, r)
                for d in exam_dates
                for r in _compatible_rooms(e, rooms)
            ]
            self.domains[e.course_code] = options

    def solve(self) -> ScheduleResult:
        import time as time_mod

        t0 = time_mod.perf_counter()
        unsat = [c for c, dom in self.domains.items() if not dom]
        if unsat:
            reasons = []
            for c in unsat:
                e = self.exams[c]
                reasons.append(
                    f"{c}: no room of correct type with capacity>={e.enrolled} "
                    f"(type={e.exam_type}, enrolled={e.enrolled})"
                )
            return ScheduleResult(
                success=False,
                hard_conflicts=reasons,
                elapsed_seconds=time_mod.perf_counter() - t0,
                courses_total=len(self.exams),
                message="Unsatisfiable domains before search",
            )

        assignment: dict[str, SlotAssignment] = {}
        order = sorted(
            self.exams.keys(),
            key=lambda c: (len(self.domains[c]), -len(self.conflict_graph.get(c, ())), -self.exams[c].enrolled),
        )

        ok = self._backtrack(order, 0, assignment)
        elapsed = time_mod.perf_counter() - t0

        if not ok:
            return ScheduleResult(
                success=False,
                hard_conflicts=["Search exhausted without a complete feasible schedule"],
                elapsed_seconds=elapsed,
                courses_scheduled=len(assignment),
                courses_total=len(self.exams),
                message="CSP failed",
                assignments=list(assignment.values()),
            )

        # Validate all hard constraints once more
        conflicts = validate_schedule(list(assignment.values()), self.conflict_graph)
        return ScheduleResult(
            success=len(conflicts) == 0,
            assignments=sorted(
                assignment.values(),
                key=lambda a: (a.exam_date, a.start_time, a.course_code),
            ),
            hard_conflicts=conflicts,
            elapsed_seconds=elapsed,
            courses_scheduled=len(assignment),
            courses_total=len(self.exams),
            message="OK" if not conflicts else "Validation found conflicts",
        )

    def _backtrack(
        self,
        order: list[str],
        idx: int,
        assignment: dict[str, SlotAssignment],
    ) -> bool:
        if idx >= len(order):
            return True

        # MRV among remaining
        remaining = order[idx:]
        var = min(remaining, key=lambda c: len(self._live_domain(c, assignment)))
        # swap into position
        j = order.index(var, idx)
        order[idx], order[j] = order[j], order[idx]

        exam = self.exams[var]
        for day, room in self._live_domain(var, assignment):
            reason = _violates_hard(exam, day, room, assignment, self.conflict_graph)
            if reason:
                continue
            start = _parse_hhmm(exam.session_time)
            end = _add_hours(start, exam.duration_hours)
            assignment[var] = SlotAssignment(
                course_code=var,
                exam_date=day.isoformat(),
                start_time=exam.session_time,
                end_time=end.strftime("%H:%M"),
                room_id=room.room_id,
                exam_type=exam.exam_type,
                enrolled=exam.enrolled,
                year_level=exam.year_level,
                lecturer_staff_id=exam.lecturer_staff_id,
            )
            if self._backtrack(order, idx + 1, assignment):
                return True
            del assignment[var]
        return False

    def _live_domain(
        self, course_code: str, assignment: dict[str, SlotAssignment]
    ) -> list[tuple[date, Room]]:
        exam = self.exams[course_code]
        live: list[tuple[date, Room]] = []
        for day, room in self.domains[course_code]:
            if _violates_hard(exam, day, room, assignment, self.conflict_graph) is None:
                live.append((day, room))
        return live


def validate_schedule(
    assignments: list[SlotAssignment],
    conflict_graph: dict[str, set[str]],
) -> list[str]:
    conflicts: list[str] = []
    by_code = {a.course_code: a for a in assignments}
    codes = list(by_code.keys())
    for i, a_code in enumerate(codes):
        a = by_code[a_code]
        a_start, a_end = _parse_hhmm(a.start_time), _parse_hhmm(a.end_time)
        for b_code in codes[i + 1 :]:
            b = by_code[b_code]
            if a.exam_date != b.exam_date:
                continue
            b_start, b_end = _parse_hhmm(b.start_time), _parse_hhmm(b.end_time)
            if not _overlaps(a_start, a_end, b_start, b_end):
                continue
            if a.room_id == b.room_id:
                conflicts.append(f"Room clash: {a_code} & {b_code} in {a.room_id}")
            if b_code in conflict_graph.get(a_code, ()):
                conflicts.append(f"Student clash: {a_code} & {b_code}")
            if (
                a.lecturer_staff_id
                and a.lecturer_staff_id == b.lecturer_staff_id
            ):
                conflicts.append(
                    f"Lecturer clash: {a.lecturer_staff_id} on {a_code} & {b_code}"
                )
    return conflicts


def run_csp(data_dir: Path | str = DEFAULT_DATA) -> ScheduleResult:
    data_dir = Path(data_dir)
    exams, rooms, graph, start, end = load_tier3(data_dir)
    dates = working_dates(start, end)
    scheduler = CSPScheduler(exams, rooms, graph, dates)
    return scheduler.solve()


def export_schedule(result: ScheduleResult, out_dir: Path | str) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "schedule.csv"
    json_path = out_dir / "schedule.json"
    fields = [
        "course_code",
        "exam_date",
        "start_time",
        "end_time",
        "room_id",
        "exam_type",
        "enrolled",
        "year_level",
        "lecturer_staff_id",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for a in result.assignments:
            writer.writerow(asdict(a))
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)
    report = out_dir / "conflict_report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write(f"success={result.success}\n")
        f.write(f"scheduled={result.courses_scheduled}/{result.courses_total}\n")
        f.write(f"elapsed_seconds={result.elapsed_seconds}\n")
        f.write(f"hard_conflicts={len(result.hard_conflicts)}\n")
        for c in result.hard_conflicts:
            f.write(f"- {c}\n")
        if not result.hard_conflicts:
            f.write("- none\n")
    return csv_path, json_path


if __name__ == "__main__":
    result = run_csp()
    out = REPO_ROOT / "data" / "tier3" / "output"
    export_schedule(result, out)
    print(
        f"success={result.success} "
        f"scheduled={result.courses_scheduled}/{result.courses_total} "
        f"conflicts={len(result.hard_conflicts)} "
        f"time={result.elapsed_seconds:.3f}s"
    )
    if result.hard_conflicts:
        for c in result.hard_conflicts[:10]:
            print(" ", c)
    print(f"Wrote {out}")
