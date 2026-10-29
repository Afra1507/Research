"""Unit tests for Module D — human resource allocator."""

from __future__ import annotations

import math
import sys
import unittest
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from engine.hr_allocator import (  # noqa: E402
    allocate_staff,
    export_hr_result,
    load_schedule_csv,
    load_staff,
    required_roles,
    run_hr_allocator,
    SESSION_INDEX,
)
from engine.csp_solver import _overlaps, _parse_hhmm  # noqa: E402


class TestRoleRatios(unittest.TestCase):
    def test_theory_ratios(self):
        r = required_roles("Theory", 85)
        self.assertEqual(r.chief_supervisors, 1)
        self.assertEqual(r.invigilators, math.ceil(85 / 30))
        self.assertEqual(r.hall_attendants, math.ceil(85 / 60))
        self.assertEqual(r.technical_officers, 0)

    def test_practical_ratios(self):
        r = required_roles("Practical", 55)
        self.assertEqual(r.chief_supervisors, 1)
        self.assertEqual(r.invigilators, math.ceil(55 / 15))
        self.assertEqual(r.hall_attendants, math.ceil(55 / 40))
        self.assertEqual(r.technical_officers, 1)


class TestHRAllocator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_hr_allocator(ROOT / "data" / "tier3", prefer_ga=True)

    def test_success(self):
        self.assertTrue(self.result.success, msg=self.result.unfilled)

    def test_no_unfilled(self):
        self.assertEqual(self.result.unfilled, [])

    def test_duties_created(self):
        self.assertGreater(len(self.result.duties), 0)

    def test_no_overlapping_duties_per_staff(self):
        by_staff = defaultdict(list)
        for d in self.result.duties:
            by_staff[d.staff_id].append(d)
        for sid, duties in by_staff.items():
            for i, a in enumerate(duties):
                for b in duties[i + 1 :]:
                    if a.exam_date != b.exam_date:
                        continue
                    self.assertFalse(
                        _overlaps(
                            _parse_hhmm(a.start_time),
                            _parse_hhmm(a.end_time),
                            _parse_hhmm(b.start_time),
                            _parse_hhmm(b.end_time),
                        ),
                        msg=f"{sid} overlap {a.course_code}/{b.course_code}",
                    )
                    # rest session: indices must differ by >= 2
                    ia = SESSION_INDEX.get(a.start_time, 0)
                    ib = SESSION_INDEX.get(b.start_time, 0)
                    self.assertGreaterEqual(
                        abs(ia - ib),
                        2,
                        msg=f"{sid} no rest between {a.start_time} and {b.start_time}",
                    )

    def test_lecturer_not_on_own_course(self):
        schedule = load_schedule_csv(ROOT / "data" / "tier3" / "output" / "schedule_ga.csv")
        lecturer = {a.course_code: a.lecturer_staff_id for a in schedule}
        for d in self.result.duties:
            lec = lecturer.get(d.course_code)
            if lec:
                self.assertNotEqual(d.staff_id, lec)

    def test_ratios_met_per_exam(self):
        schedule = load_schedule_csv(ROOT / "data" / "tier3" / "output" / "schedule_ga.csv")
        by_course = {a.course_code: a for a in schedule}
        duties_by_course = defaultdict(list)
        for d in self.result.duties:
            duties_by_course[d.course_code].append(d)
        for code, exam in by_course.items():
            req = required_roles(exam.exam_type, exam.enrolled)
            roles = [d.duty_role for d in duties_by_course[code]]
            self.assertEqual(roles.count("ChiefSupervisor"), req.chief_supervisors)
            self.assertEqual(roles.count("Invigilator"), req.invigilators)
            self.assertEqual(roles.count("HallAttendant"), req.hall_attendants)
            self.assertEqual(roles.count("TechnicalOfficer"), req.technical_officers)

    def test_balance_metric(self):
        self.assertGreaterEqual(self.result.duty_balance_std, 0.0)

    def test_export(self):
        out = ROOT / "data" / "tier3" / "output"
        path = export_hr_result(self.result, out)
        self.assertTrue(path.exists())
        self.assertTrue((out / "hr_report.txt").exists())


if __name__ == "__main__":
    unittest.main()
