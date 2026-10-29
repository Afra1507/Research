"""Unit tests for Module E — resource calculator."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from engine.resource_calc import (  # noqa: E402
    _copies_with_buffer,
    calculate_resources,
    export_resource_result,
    load_stationery_norms,
    run_resource_calculator,
)
from engine.hr_allocator import load_schedule_csv  # noqa: E402
from engine.csp_solver import SlotAssignment  # noqa: E402


class TestBufferMath(unittest.TestCase):
    def test_theory_5_percent(self):
        # 100 students → ceil(105) = 105
        self.assertEqual(_copies_with_buffer(100, 5), 105)

    def test_practical_3_percent(self):
        self.assertEqual(_copies_with_buffer(55, 3), math.ceil(55 * 1.03))


class TestResourceCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_resource_calculator(ROOT / "data" / "tier3", prefer_ga=True)

    def test_success(self):
        self.assertTrue(self.result.success)

    def test_lines_for_all_exams(self):
        schedule = load_schedule_csv(ROOT / "data" / "tier3" / "output" / "schedule_ga.csv")
        # 3 stationery items per exam type
        self.assertEqual(len(self.result.lines), len(schedule) * 3)

    def test_buffers_match_exam_type(self):
        for line in self.result.lines:
            if line.exam_type == "Theory":
                self.assertEqual(line.buffer_pct, 5.0)
            else:
                self.assertEqual(line.buffer_pct, 3.0)

    def test_single_exam_example(self):
        exam = SlotAssignment(
            course_code="CSC 315",
            exam_date="2025-01-10",
            start_time="13:00",
            end_time="14:30",
            room_id="FOC-LH-01",
            exam_type="Theory",
            enrolled=100,
            year_level=3,
            lecturer_staff_id="S001",
        )
        norms = load_stationery_norms(ROOT / "data" / "tier3")
        result = calculate_resources([exam], norms)
        qp = next(x for x in result.lines if x.item == "Question paper")
        self.assertEqual(qp.copies, 105)
        self.assertEqual(qp.sheets_total, 105 * 4)

    def test_procurement_aggregated(self):
        self.assertIn("Question paper", self.result.procurement)
        self.assertIn("Answer booklet", self.result.procurement)
        self.assertIn("Cover sheet", self.result.procurement)
        self.assertGreater(self.result.totals["sheets_total"], 0)
        self.assertGreater(self.result.totals["reams_total"], 0)

    def test_beats_or_equals_naive_baseline(self):
        self.assertLessEqual(
            self.result.baseline_comparison["precise_sheets_total"],
            self.result.baseline_comparison["baseline_sheets_total"],
        )

    def test_export(self):
        out = ROOT / "data" / "tier3" / "output"
        path = export_resource_result(self.result, out)
        self.assertTrue(path.exists())
        self.assertTrue((out / "procurement_report.csv").exists())
        self.assertTrue((out / "resource_report.txt").exists())


if __name__ == "__main__":
    unittest.main()
