"""Unit tests for Module C — Genetic Algorithm optimiser."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from engine.csp_solver import run_csp, validate_schedule, load_tier3  # noqa: E402
from engine.ga_optimiser import run_ga, export_ga_result, evaluate_fitness, _load_students  # noqa: E402
from engine.csp_solver import working_dates  # noqa: E402


class TestGAOptimiser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = ROOT / "data" / "tier3"
        cls.csp = run_csp(data)
        # Smaller GA for unit-test speed; still 5 runs as per proposal
        cls.ga = run_ga(
            data,
            csp_result=cls.csp,
            n_runs=5,
            population_size=20,
            generations=25,
            base_seed=42,
        )

    def test_csp_seed_ok(self):
        self.assertTrue(self.csp.success)

    def test_ga_success_zero_hard_conflicts(self):
        self.assertTrue(self.ga.success, msg=self.ga.hard_conflicts)
        self.assertEqual(self.ga.hard_conflicts, [])

    def test_all_courses_retained(self):
        self.assertEqual(len(self.ga.assignments), self.csp.courses_total)

    def test_fitness_not_worse(self):
        self.assertGreaterEqual(
            self.ga.fitness_after.total + 1e-9,
            self.ga.fitness_before.total,
        )

    def test_five_runs_recorded(self):
        self.assertEqual(len(self.ga.run_fitness), 5)
        self.assertGreaterEqual(self.ga.best_run_index, 0)

    def test_year_sessions_preserved(self):
        expected = {1: "08:00", 2: "10:00", 3: "13:00", 4: "15:30"}
        for a in self.ga.assignments:
            self.assertEqual(a.start_time, expected[a.year_level])

    def test_revalidate_graph(self):
        _, _, graph, _, _ = load_tier3(ROOT / "data" / "tier3")
        self.assertEqual(validate_schedule(self.ga.assignments, graph), [])

    def test_export(self):
        out = ROOT / "data" / "tier3" / "output"
        path = export_ga_result(self.ga, out)
        self.assertTrue(path.exists())
        self.assertTrue((out / "ga_summary.json").exists())
        self.assertTrue((out / "ga_report.txt").exists())


if __name__ == "__main__":
    unittest.main()
