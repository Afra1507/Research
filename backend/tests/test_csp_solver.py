"""Unit tests for Module B — CSP scheduling engine."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from engine.csp_solver import (  # noqa: E402
    run_csp,
    validate_schedule,
    export_schedule,
    load_tier3,
)


class TestCSPSolver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_csp(ROOT / "data" / "tier3")

    def test_success(self):
        self.assertTrue(
            self.result.success,
            msg=self.result.hard_conflicts or self.result.message,
        )

    def test_all_courses_scheduled(self):
        self.assertEqual(self.result.courses_scheduled, self.result.courses_total)
        self.assertEqual(self.result.courses_total, 53)

    def test_zero_hard_conflicts(self):
        self.assertEqual(self.result.hard_conflicts, [])

    def test_under_60_seconds(self):
        self.assertLess(self.result.elapsed_seconds, 60.0)

    def test_year_session_times(self):
        expected = {1: "08:00", 2: "10:00", 3: "13:00", 4: "15:30"}
        for a in self.result.assignments:
            self.assertEqual(a.start_time, expected[a.year_level])

    def test_revalidate_with_graph(self):
        _, _, graph, _, _ = load_tier3(ROOT / "data" / "tier3")
        conflicts = validate_schedule(self.result.assignments, graph)
        self.assertEqual(conflicts, [])

    def test_export(self):
        out = ROOT / "data" / "tier3" / "output"
        csv_path, json_path = export_schedule(self.result, out)
        self.assertTrue(csv_path.exists())
        self.assertTrue(json_path.exists())
        self.assertTrue((out / "conflict_report.txt").exists())


if __name__ == "__main__":
    unittest.main()
