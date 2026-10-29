"""
Module C — Genetic Algorithm optimiser (soft constraints).

Takes a feasible CSP schedule and searches neighbouring feasible schedules
to improve soft objectives, without violating hard constraints.

Soft objectives (higher fitness is better):
  1. Even spread of exams across the examination period
  2. Fewer same-day consecutive exams for the same student
  3. Prefer earlier dates for large-enrolment courses
  4. More even lecturer exam-day load

Reports the best individual from ``n_runs`` independent GA runs (default 5).
"""

from __future__ import annotations

import csv
import json
import random
import statistics
import time as time_mod
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

try:
    from .csp_solver import (
        DEFAULT_DATA,
        REPO_ROOT,
        CSPScheduler,
        CourseExam,
        Room,
        ScheduleResult,
        SlotAssignment,
        _add_hours,
        _parse_hhmm,
        _violates_hard,
        export_schedule,
        load_tier3,
        run_csp,
        validate_schedule,
        working_dates,
    )
except ImportError:  # running as a script
    from csp_solver import (  # type: ignore
        DEFAULT_DATA,
        REPO_ROOT,
        CSPScheduler,
        CourseExam,
        Room,
        ScheduleResult,
        SlotAssignment,
        _add_hours,
        _parse_hhmm,
        _violates_hard,
        export_schedule,
        load_tier3,
        run_csp,
        validate_schedule,
        working_dates,
    )

DEFAULT_WEIGHTS = {
    "day_balance": 1.0,
    "student_gaps": 1.2,
    "large_early": 0.8,
    "lecturer_balance": 0.6,
}


@dataclass
class FitnessBreakdown:
    total: float
    day_balance: float
    student_gaps: float
    large_early: float
    lecturer_balance: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class GAResult:
    success: bool
    assignments: list[SlotAssignment]
    hard_conflicts: list[str]
    fitness_before: FitnessBreakdown
    fitness_after: FitnessBreakdown
    best_run_index: int
    run_fitness: list[float]
    generations: int
    population_size: int
    elapsed_seconds: float
    message: str = ""

    def to_schedule_result(self) -> ScheduleResult:
        return ScheduleResult(
            success=self.success and not self.hard_conflicts,
            assignments=self.assignments,
            hard_conflicts=self.hard_conflicts,
            elapsed_seconds=self.elapsed_seconds,
            courses_scheduled=len(self.assignments),
            courses_total=len(self.assignments),
            message=self.message,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "best_run_index": self.best_run_index,
            "run_fitness": self.run_fitness,
            "generations": self.generations,
            "population_size": self.population_size,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "fitness_before": self.fitness_before.to_dict(),
            "fitness_after": self.fitness_after.to_dict(),
            "hard_conflicts": self.hard_conflicts,
            "assignments": [asdict(a) for a in self.assignments],
        }


def _assignment_map(assignments: list[SlotAssignment]) -> dict[str, SlotAssignment]:
    return {a.course_code: a for a in assignments}


def _make_assignment(exam: CourseExam, day: date, room: Room) -> SlotAssignment:
    start = _parse_hhmm(exam.session_time)
    end = _add_hours(start, exam.duration_hours)
    return SlotAssignment(
        course_code=exam.course_code,
        exam_date=day.isoformat(),
        start_time=exam.session_time,
        end_time=end.strftime("%H:%M"),
        room_id=room.room_id,
        exam_type=exam.exam_type,
        enrolled=exam.enrolled,
        year_level=exam.year_level,
        lecturer_staff_id=exam.lecturer_staff_id,
    )


def evaluate_fitness(
    assignments: list[SlotAssignment],
    *,
    students_by_course: dict[str, set[str]],
    exam_dates: list[date],
    weights: Optional[dict[str, float]] = None,
) -> FitnessBreakdown:
    """Soft-constraint fitness in roughly [0, sum(weights)] scale."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    if not assignments:
        return FitnessBreakdown(0, 0, 0, 0, 0)

    date_set = [d.isoformat() for d in exam_dates]
    counts = {d: 0 for d in date_set}
    for a in assignments:
        if a.exam_date in counts:
            counts[a.exam_date] += 1
    vals = list(counts.values())
    std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    day_balance = 1.0 / (1.0 + std)

    course_assign = _assignment_map(assignments)
    student_courses: dict[str, list[str]] = defaultdict(list)
    for code, students in students_by_course.items():
        if code not in course_assign:
            continue
        for sid in students:
            student_courses[sid].append(code)

    penalty = 0.0
    scored = 0
    for _sid, codes in student_courses.items():
        if len(codes) < 2:
            continue
        by_day: dict[str, list[SlotAssignment]] = defaultdict(list)
        for c in codes:
            by_day[course_assign[c].exam_date].append(course_assign[c])
        for day_exams in by_day.values():
            if len(day_exams) < 2:
                continue
            scored += 1
            day_exams = sorted(day_exams, key=lambda a: a.start_time)
            for i in range(len(day_exams) - 1):
                a, b = day_exams[i], day_exams[i + 1]
                end_a = datetime.combine(date.today(), _parse_hhmm(a.end_time))
                start_b = datetime.combine(date.today(), _parse_hhmm(b.start_time))
                gap_h = (start_b - end_a).total_seconds() / 3600.0
                if gap_h < 0:
                    penalty += 5.0
                elif gap_h < 1.0:
                    penalty += 2.0
                elif gap_h < 2.0:
                    penalty += 1.0
                else:
                    penalty += 0.25
            penalty += 0.5 * (len(day_exams) - 1)

    student_gaps = 1.0 if scored == 0 else 1.0 / (1.0 + penalty / max(scored, 1))

    index = {d.isoformat(): i for i, d in enumerate(exam_dates)}
    pairs = [
        (a.enrolled, index.get(a.exam_date, len(exam_dates) // 2))
        for a in assignments
    ]
    if len(pairs) >= 2:
        enr = [p[0] for p in pairs]
        idx = [p[1] for p in pairs]
        mean_e, mean_i = statistics.fmean(enr), statistics.fmean(idx)
        num = sum((e - mean_e) * (i - mean_i) for e, i in zip(enr, idx))
        den_e = sum((e - mean_e) ** 2 for e in enr) ** 0.5
        den_i = sum((i - mean_i) ** 2 for i in idx) ** 0.5
        if den_e > 0 and den_i > 0:
            corr = num / (den_e * den_i)
            large_early = (1.0 - corr) / 2.0
        else:
            large_early = 0.5
    else:
        large_early = 0.5

    lec_counts: dict[str, int] = defaultdict(int)
    for a in assignments:
        if a.lecturer_staff_id:
            lec_counts[a.lecturer_staff_id] += 1
    if len(lec_counts) >= 2:
        lecturer_balance = 1.0 / (1.0 + statistics.pstdev(lec_counts.values()))
    else:
        lecturer_balance = 1.0

    total = (
        w["day_balance"] * day_balance
        + w["student_gaps"] * student_gaps
        + w["large_early"] * large_early
        + w["lecturer_balance"] * lecturer_balance
    )
    return FitnessBreakdown(
        total=total,
        day_balance=day_balance,
        student_gaps=student_gaps,
        large_early=large_early,
        lecturer_balance=lecturer_balance,
    )


class GeneticOptimiser:
    def __init__(
        self,
        exams: list[CourseExam],
        rooms: list[Room],
        conflict_graph: dict[str, set[str]],
        exam_dates: list[date],
        students_by_course: dict[str, set[str]],
        *,
        population_size: int = 40,
        generations: int = 60,
        mutation_rate: float = 0.25,
        elite: int = 2,
        tournament_k: int = 3,
        weights: Optional[dict[str, float]] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.exams = {e.course_code: e for e in exams}
        self.rooms = {r.room_id: r for r in rooms}
        self.conflict_graph = conflict_graph
        self.exam_dates = exam_dates
        self.students_by_course = students_by_course
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elite = elite
        self.tournament_k = tournament_k
        self.weights = weights
        self.rng = random.Random(seed)
        scheduler = CSPScheduler(exams, rooms, conflict_graph, exam_dates)
        self.domains = scheduler.domains

    def _fitness(self, individual: dict[str, SlotAssignment]) -> FitnessBreakdown:
        return evaluate_fitness(
            list(individual.values()),
            students_by_course=self.students_by_course,
            exam_dates=self.exam_dates,
            weights=self.weights,
        )

    def _clone(self, individual: dict[str, SlotAssignment]) -> dict[str, SlotAssignment]:
        return dict(individual)

    def _is_feasible(self, individual: dict[str, SlotAssignment]) -> bool:
        return not validate_schedule(list(individual.values()), self.conflict_graph)

    def _mutate(self, individual: dict[str, SlotAssignment]) -> dict[str, SlotAssignment]:
        child = self._clone(individual)
        codes = list(child.keys())
        self.rng.shuffle(codes)
        mutations = max(1, int(len(codes) * self.mutation_rate))
        for code in codes[:mutations]:
            exam = self.exams[code]
            options = list(self.domains.get(code, []))
            self.rng.shuffle(options)
            others = {k: v for k, v in child.items() if k != code}
            for day, room in options[:25]:
                if _violates_hard(exam, day, room, others, self.conflict_graph):
                    continue
                child[code] = _make_assignment(exam, day, room)
                break
        return child

    def _crossover(
        self,
        a: dict[str, SlotAssignment],
        b: dict[str, SlotAssignment],
    ) -> dict[str, SlotAssignment]:
        child: dict[str, SlotAssignment] = {}
        for code in a:
            child[code] = a[code] if self.rng.random() < 0.5 else b[code]
        for code in list(child.keys()):
            exam = self.exams[code]
            others = {k: v for k, v in child.items() if k != code}
            day = date.fromisoformat(child[code].exam_date)
            room = self.rooms[child[code].room_id]
            if _violates_hard(exam, day, room, others, self.conflict_graph) is None:
                continue
            options = list(self.domains.get(code, []))
            self.rng.shuffle(options)
            repaired = False
            for d, r in options:
                if _violates_hard(exam, d, r, others, self.conflict_graph) is None:
                    child[code] = _make_assignment(exam, d, r)
                    repaired = True
                    break
            if not repaired:
                child[code] = a[code]
        return child

    def _tournament(
        self, population: list[dict[str, SlotAssignment]], scores: list[float]
    ) -> dict[str, SlotAssignment]:
        picks = self.rng.sample(
            range(len(population)), k=min(self.tournament_k, len(population))
        )
        best = max(picks, key=lambda i: scores[i])
        return population[best]

    def evolve(
        self, seed_individual: dict[str, SlotAssignment]
    ) -> tuple[dict[str, SlotAssignment], FitnessBreakdown]:
        population = [self._clone(seed_individual)]
        while len(population) < self.population_size:
            population.append(self._mutate(seed_individual))

        scores = [self._fitness(ind).total for ind in population]
        best_idx = max(range(len(population)), key=lambda i: scores[i])
        best = self._clone(population[best_idx])
        best_fit = self._fitness(best)

        for _gen in range(self.generations):
            ranked = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)
            new_pop = [self._clone(population[i]) for i in ranked[: self.elite]]
            while len(new_pop) < self.population_size:
                p1 = self._tournament(population, scores)
                p2 = self._tournament(population, scores)
                child = self._crossover(p1, p2)
                if self.rng.random() < 0.8:
                    child = self._mutate(child)
                if not self._is_feasible(child):
                    child = self._mutate(p1)
                new_pop.append(child)

            population = new_pop
            scores = [self._fitness(ind).total for ind in population]
            gen_best_i = max(range(len(population)), key=lambda i: scores[i])
            if scores[gen_best_i] > best_fit.total + 1e-12:
                best = self._clone(population[gen_best_i])
                best_fit = self._fitness(best)

        return best, best_fit


def _load_students(data_dir: Path) -> dict[str, set[str]]:
    students_by_course: dict[str, set[str]] = defaultdict(set)
    with (data_dir / "enrolments.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            students_by_course[row["course_code"]].add(row["anon_student_id"])
    return students_by_course


def run_ga(
    data_dir: Path | str = DEFAULT_DATA,
    *,
    csp_result: Optional[ScheduleResult] = None,
    n_runs: int = 5,
    population_size: int = 40,
    generations: int = 60,
    base_seed: int = 20261029,
) -> GAResult:
    data_dir = Path(data_dir)
    t0 = time_mod.perf_counter()

    if csp_result is None:
        csp_result = run_csp(data_dir)
    if not csp_result.success:
        empty = FitnessBreakdown(0, 0, 0, 0, 0)
        return GAResult(
            success=False,
            assignments=csp_result.assignments,
            hard_conflicts=csp_result.hard_conflicts,
            fitness_before=empty,
            fitness_after=empty,
            best_run_index=-1,
            run_fitness=[],
            generations=generations,
            population_size=population_size,
            elapsed_seconds=time_mod.perf_counter() - t0,
            message="CSP seed schedule failed; GA not run",
        )

    exams, rooms, graph, start, end = load_tier3(data_dir)
    dates = working_dates(start, end)
    students = _load_students(data_dir)
    seed_map = _assignment_map(csp_result.assignments)

    fitness_before = evaluate_fitness(
        csp_result.assignments,
        students_by_course=students,
        exam_dates=dates,
    )

    run_fitness: list[float] = []
    best_overall: Optional[dict[str, SlotAssignment]] = None
    best_fit: Optional[FitnessBreakdown] = None
    best_run = -1

    for run in range(n_runs):
        opt = GeneticOptimiser(
            exams,
            rooms,
            graph,
            dates,
            students,
            population_size=population_size,
            generations=generations,
            seed=base_seed + run * 97,
        )
        individual, fit = opt.evolve(seed_map)
        run_fitness.append(fit.total)
        if best_fit is None or fit.total > best_fit.total:
            best_fit = fit
            best_overall = individual
            best_run = run

    assert best_overall is not None and best_fit is not None
    assignments = sorted(
        best_overall.values(),
        key=lambda a: (a.exam_date, a.start_time, a.course_code),
    )
    hard = validate_schedule(assignments, graph)
    elapsed = time_mod.perf_counter() - t0

    return GAResult(
        success=len(hard) == 0,
        assignments=assignments,
        hard_conflicts=hard,
        fitness_before=fitness_before,
        fitness_after=best_fit,
        best_run_index=best_run,
        run_fitness=run_fitness,
        generations=generations,
        population_size=population_size,
        elapsed_seconds=elapsed,
        message=(
            f"GA best of {n_runs} runs; "
            f"fitness {fitness_before.total:.4f} → {best_fit.total:.4f}"
        ),
    )


def export_ga_result(result: GAResult, out_dir: Path | str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    export_schedule(result.to_schedule_result(), out_dir)

    ga_csv = out_dir / "schedule_ga.csv"
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
    with ga_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for a in result.assignments:
            writer.writerow(asdict(a))

    with (out_dir / "ga_summary.json").open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    with (out_dir / "ga_report.txt").open("w", encoding="utf-8") as f:
        f.write(result.message + "\n")
        f.write(f"success={result.success}\n")
        f.write(f"hard_conflicts={len(result.hard_conflicts)}\n")
        f.write(f"best_run_index={result.best_run_index}\n")
        f.write(f"run_fitness={result.run_fitness}\n")
        f.write(f"fitness_before={result.fitness_before.to_dict()}\n")
        f.write(f"fitness_after={result.fitness_after.to_dict()}\n")
        f.write(f"elapsed_seconds={result.elapsed_seconds:.3f}\n")
    return ga_csv


if __name__ == "__main__":
    result = run_ga(n_runs=5, generations=40, population_size=30)
    out = REPO_ROOT / "data" / "tier3" / "output"
    export_ga_result(result, out)
    print(result.message)
    print(
        f"success={result.success} hard={len(result.hard_conflicts)} "
        f"time={result.elapsed_seconds:.2f}s best_run={result.best_run_index}"
    )
    print("before:", result.fitness_before.to_dict())
    print("after: ", result.fitness_after.to_dict())
