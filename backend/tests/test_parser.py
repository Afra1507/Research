"""Unit tests for Module A — course code parser."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from engine.parser import (  # noqa: E402
    CourseParseError,
    parse_course,
    parse_course_code_string,
    parse_courses_csv,
)

TIER3_COURSES = ROOT / "data" / "tier3" / "courses.csv"


class TestCombinedString(unittest.TestCase):
    def test_csc_315_2_0(self):
        p = parse_course_code_string("CSC 315 2.0")
        self.assertEqual(p.department_code, "CSC")
        self.assertEqual(p.course_code, "CSC 315")
        self.assertEqual(p.module_number, "315")
        self.assertEqual(p.year_level, 3)
        self.assertEqual(p.module_seq, "15")
        self.assertEqual(p.credits, 2.0)
        self.assertEqual(p.duration_hours, 2.0)
        self.assertEqual(p.session_time, "13:00")

    def test_whitespace_normalized(self):
        p = parse_course_code_string("  csc   316   1.5 ")
        self.assertEqual(p.department_code, "CSC")
        self.assertEqual(p.course_code, "CSC 316")
        self.assertEqual(p.credits, 1.5)
        self.assertEqual(p.year_level, 3)

    def test_year_sessions(self):
        self.assertEqual(parse_course_code_string("CSC 101 1.0").session_time, "08:00")
        self.assertEqual(parse_course_code_string("CSC 201 1.0").session_time, "10:00")
        self.assertEqual(parse_course_code_string("CSC 301 1.0").session_time, "13:00")
        self.assertEqual(parse_course_code_string("CSC 401 1.0").session_time, "15:30")

    def test_missing_credits_raises(self):
        with self.assertRaises(CourseParseError):
            parse_course_code_string("CSC 315")

    def test_invalid_credits_raises(self):
        with self.assertRaises(CourseParseError):
            parse_course_code_string("CSC 315 2.5")


class TestFieldForm(unittest.TestCase):
    def test_code_plus_credits(self):
        p = parse_course(course_code="CSC 355", credits=2.0, course_name="Machine Learning Foundations")
        self.assertEqual(p.course_code, "CSC 355")
        self.assertEqual(p.year_level, 3)
        self.assertEqual(p.credits, 2.0)
        self.assertEqual(p.exam_type, "Theory")
        self.assertEqual(p.source, "fields")

    def test_practical_from_name(self):
        p = parse_course(
            course_code="CSC 111",
            credits=1.5,
            course_name="Programming Laboratory",
        )
        self.assertEqual(p.exam_type, "Practical")

    def test_explicit_exam_type(self):
        p = parse_course(
            course_code="CSC 111",
            credits=1.5,
            course_name="Programming Laboratory",
            exam_type="Theory",
        )
        self.assertEqual(p.exam_type, "Theory")

    def test_raw_alias(self):
        p = parse_course(raw="CSC 315 1.5")
        self.assertEqual(p.year_level, 3)
        self.assertEqual(p.credits, 1.5)


class TestTier3Csv(unittest.TestCase):
    def test_all_tier3_courses_parse(self):
        self.assertTrue(TIER3_COURSES.exists(), f"Missing {TIER3_COURSES}")
        parsed = parse_courses_csv(TIER3_COURSES)
        self.assertEqual(len(parsed), 53)

        import csv

        with TIER3_COURSES.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        for row, p in zip(rows, parsed):
            self.assertEqual(p.course_code, row["course_code"])
            self.assertEqual(p.year_level, int(row["year_level"]))
            self.assertEqual(p.credits, float(row["credits"]))
            self.assertEqual(p.session_time, row["session_time"])
            self.assertEqual(p.exam_type, row["exam_type"])
            self.assertEqual(p.duration_hours, float(row["duration_hours"]))
            # Year digit must match leading digit of module number
            module = row["course_code"].split()[1]
            self.assertEqual(p.year_level, int(module[0]))


if __name__ == "__main__":
    unittest.main()
