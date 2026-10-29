"""
Tier 3 synthetic dataset generator — USJ Faculty of Computing, CSC department only.

Campus conventions modelled:
  - Student index: AS2022468 → AS + intake year (2022) + 3-digit serial (468)
  - Course code:   CSC 315 → dept + space + 3-digit module (leading digit = year)
  - Credits:       1.0 / 1.5 / 2.0 only (max 2.0 for CSC written exams)
  - Scope:         Computer Science department only (no programme field)

Run from repo root: python data/tier3/generate_synthetic.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RNG = random.Random(20261029)  # reproducible

# CSC written-exam credits only (max 2.0)
CREDITS = [1.0, 1.5, 2.0]
YEAR_COHORT = {1: 175, 2: 150, 3: 110, 4: 80}
SESSION_BY_YEAR = {1: "08:00", 2: "10:00", 3: "13:00", 4: "15:30"}

# Exam period academic year 2024/2025 → intake year by study year
# Year 1 entered 2024, Year 2 entered 2023, Year 3 entered 2022, Year 4 entered 2021
INTAKE_YEAR_BY_STUDY_YEAR = {1: 2024, 2: 2023, 3: 2022, 4: 2021}

THEORY_NAMES = [
    "Fundamentals of Computing",
    "Discrete Mathematics",
    "Programming Principles",
    "Computer Systems",
    "Data Structures",
    "Database Systems",
    "Operating Systems",
    "Software Engineering",
    "Computer Networks",
    "Algorithms and Complexity",
    "Web Technologies",
    "Object Oriented Design",
    "Artificial Intelligence",
    "Machine Learning Foundations",
    "Information Security",
    "Human Computer Interaction",
    "Distributed Systems",
    "Compiler Construction",
    "Research Methods",
    "Professional Practice",
]

PRACTICAL_NAMES = [
    "Programming Laboratory",
    "Database Practical",
    "Networking Laboratory",
    "Software Project Workshop",
    "Machine Learning Laboratory",
    "Web Development Practical",
    "Systems Programming Lab",
    "HCI Design Studio",
]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_course_code(year: int, module_suffix: int) -> str:
    """CSC 315 style: leading digit = year, next two = module sequence."""
    return f"CSC {year}{module_suffix:02d}"


def build_courses() -> list[dict]:
    """
    Build CSC-only courses. Codes like CSC 101, CSC 215, CSC 315, CSC 355.
    Module suffixes are non-contiguous in places to mirror real catalogues.
    """
    courses: list[dict] = []
    theory_idx = 0
    practical_idx = 0

    # (year, list of module suffixes for theory, list for practical)
    # Mirrors real-looking gaps e.g. 15, 16, 55 in year 3
    plan = {
        1: {
            "theory": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "practical": [11, 12],
        },
        2: {
            "theory": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15],
            "practical": [16, 17],
        },
        3: {
            "theory": [1, 2, 5, 10, 14, 15, 16, 20, 25, 30, 35, 55],
            "practical": [40, 45, 50],
        },
        4: {
            "theory": [1, 2, 5, 10, 15, 20, 25, 30, 35, 40],
            "practical": [45, 50],
        },
    }

    for year, blocks in plan.items():
        for suffix in blocks["theory"]:
            name = THEORY_NAMES[theory_idx % len(THEORY_NAMES)]
            theory_idx += 1
            credits = RNG.choice(CREDITS)
            code = format_course_code(year, suffix)
            courses.append(
                {
                    "course_code": code,
                    "course_name": name,
                    "department_code": "CSC",
                    "year_level": year,
                    "semester": 2,
                    "credits": f"{credits:.1f}",
                    "exam_type": "Theory",
                    "has_theory_exam": "Y",
                    "has_practical_exam": "N",
                    "offering_status": "Active",
                    "lecturer_staff_id": "",
                    "session_time": SESSION_BY_YEAR[year],
                    "duration_hours": f"{credits:.1f}",
                }
            )
        for suffix in blocks["practical"]:
            name = PRACTICAL_NAMES[practical_idx % len(PRACTICAL_NAMES)]
            practical_idx += 1
            credits = RNG.choice([1.0, 1.5, 2.0])
            code = format_course_code(year, suffix)
            courses.append(
                {
                    "course_code": code,
                    "course_name": name,
                    "department_code": "CSC",
                    "year_level": year,
                    "semester": 2,
                    "credits": f"{credits:.1f}",
                    "exam_type": "Practical",
                    "has_theory_exam": "N",
                    "has_practical_exam": "Y",
                    "offering_status": "Active",
                    "lecturer_staff_id": "",
                    "session_time": SESSION_BY_YEAR[year],
                    "duration_hours": f"{credits:.1f}",
                }
            )
    return courses


def build_staff(n: int = 40) -> list[dict]:
    # Role flags: (designation, chief, invigilator, attendant, technical_officer)
    # Demonstrators/lecturers may also attend halls (common in SL public universities).
    designations = [
        ("Senior Lecturer", True, True, True, False),
        ("Lecturer", True, True, True, False),
        ("Lecturer", False, True, True, False),
        ("Demonstrator", False, True, True, False),
        ("Technical Officer", False, False, False, True),
        ("Admin Assistant", False, False, True, False),
    ]
    staff: list[dict] = []
    for i in range(1, n + 1):
        des, chief, inv, att, to = designations[(i - 1) % len(designations)]
        # Duty caps sized for a full CSC semester (~50 exams, multi-role per paper)
        if des == "Admin Assistant":
            max_duties = 16
        elif des == "Technical Officer":
            max_duties = 12
        else:
            max_duties = 12
        staff.append(
            {
                "staff_id": f"S{i:03d}",
                "display_name": f"Staff Member {i:03d}",
                "department": "CSC",
                "designation": des,
                "can_be_chief_supervisor": "Y" if chief else "N",
                "can_be_invigilator": "Y" if inv else "N",
                "can_be_hall_attendant": "Y" if att else "N",
                "can_be_technical_officer": "Y" if to else "N",
                "max_duties_per_period": max_duties,
                "unavailable_slots": "",
                "teaches_course_codes": "",
            }
        )
    return staff


def assign_lecturers(courses: list[dict], staff: list[dict]) -> None:
    lecturers = [
        s for s in staff if s["designation"] in ("Senior Lecturer", "Lecturer")
    ]
    taught: dict[str, list[str]] = {s["staff_id"]: [] for s in lecturers}
    for course in courses:
        lec = RNG.choice(lecturers)
        course["lecturer_staff_id"] = lec["staff_id"]
        taught[lec["staff_id"]].append(course["course_code"])
    for s in staff:
        if s["staff_id"] in taught:
            s["teaches_course_codes"] = ";".join(taught[s["staff_id"]])


def build_rooms() -> list[dict]:
    rooms = []
    for i, cap in enumerate([200, 180, 150, 120], start=1):
        rooms.append(
            {
                "room_id": f"FOC-LH-{i:02d}",
                "room_name": f"Lecture Hall {i}",
                "building": "Faculty of Computing",
                "capacity": cap,
                "room_type": "ExamHall",
                "exam_usable": "Y",
                "facilities": "desks,projector",
                "available_for_exams": "Y",
            }
        )
    for i, cap in enumerate([80, 70, 60, 55, 50], start=1):
        rooms.append(
            {
                "room_id": f"FOC-MH-{i:02d}",
                "room_name": f"Medium Hall {i}",
                "building": "Faculty of Computing",
                "capacity": cap,
                "room_type": "LectureHall",
                "exam_usable": "Y",
                "facilities": "desks",
                "available_for_exams": "Y",
            }
        )
    for i, cap in enumerate([60, 40], start=1):
        rooms.append(
            {
                "room_id": f"FOC-LAB-{i:02d}",
                "room_name": f"Computer Lab {i}",
                "building": "Faculty of Computing",
                "capacity": cap,
                "room_type": "ComputerLab",
                "exam_usable": "Y",
                "facilities": "PCs,projector",
                "available_for_exams": "Y",
            }
        )
    return rooms


def make_student_id(intake_year: int, serial: int) -> str:
    """AS2022468 style: AS + 4-digit intake year + 3-digit serial."""
    return f"AS{intake_year}{serial:03d}"


def build_enrolments(courses: list[dict]) -> list[dict]:
    students_by_year: dict[int, list[str]] = {}
    # Starting serials chosen so formats look realistic (e.g. AS2022468 in Y3 cohort)
    serial_start = {1: 1, 2: 50, 3: 400, 4: 20}
    for year, size in YEAR_COHORT.items():
        intake = INTAKE_YEAR_BY_STUDY_YEAR[year]
        start = serial_start[year]
        students_by_year[year] = [
            make_student_id(intake, start + i) for i in range(size)
        ]

    rows: list[dict] = []
    courses_by_year: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    for c in courses:
        courses_by_year[int(c["year_level"])].append(c)

    for year, year_courses in courses_by_year.items():
        students = students_by_year[year]
        for sid in students:
            k = RNG.randint(4, min(6, len(year_courses)))
            chosen = RNG.sample(year_courses, k=k)
            for c in chosen:
                rows.append(
                    {
                        "anon_student_id": sid,
                        "course_code": c["course_code"],
                        "academic_year": "2024/2025",
                        "semester": 2,
                    }
                )

        if year in (3, 4) and year_courses:
            other_year = 3 if year == 4 else 4
            other_students = students_by_year[other_year]
            elective = year_courses[0]
            for sid in RNG.sample(other_students, k=min(15, len(other_students))):
                rows.append(
                    {
                        "anon_student_id": sid,
                        "course_code": elective["course_code"],
                        "academic_year": "2024/2025",
                        "semester": 2,
                    }
                )

    seen = set()
    unique = []
    for r in rows:
        key = (r["anon_student_id"], r["course_code"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # Cap practical enrolments so they fit ComputerLab capacity (hard CSP constraint)
    practical_codes = {c["course_code"] for c in courses if c["exam_type"] == "Practical"}
    max_practical = 55  # largest lab is 60; leave headroom
    by_course: dict[str, list[dict]] = {}
    for r in unique:
        by_course.setdefault(r["course_code"], []).append(r)
    capped: list[dict] = []
    for code, erows in by_course.items():
        if code in practical_codes and len(erows) > max_practical:
            capped.extend(RNG.sample(erows, k=max_practical))
        else:
            capped.extend(erows)
    return capped


def enrolment_counts(enrolments: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for r in enrolments:
        counts[r["course_code"]] = counts.get(r["course_code"], 0) + 1
    return [
        {
            "course_code": code,
            "academic_year": "2024/2025",
            "semester": 2,
            "registered_count": n,
            "exam_eligible_count": max(0, n - RNG.randint(0, min(5, n // 20 + 1))),
        }
        for code, n in sorted(counts.items())
    ]


def main() -> None:
    courses = build_courses()
    staff = build_staff(40)
    assign_lecturers(courses, staff)
    rooms = build_rooms()
    enrolments = build_enrolments(courses)
    counts = enrolment_counts(enrolments)

    write_csv(
        ROOT / "courses.csv",
        [
            "course_code",
            "course_name",
            "department_code",
            "year_level",
            "semester",
            "credits",
            "exam_type",
            "has_theory_exam",
            "has_practical_exam",
            "offering_status",
            "lecturer_staff_id",
            "session_time",
            "duration_hours",
        ],
        courses,
    )
    write_csv(
        ROOT / "enrolments.csv",
        ["anon_student_id", "course_code", "academic_year", "semester"],
        enrolments,
    )
    write_csv(
        ROOT / "enrolment_counts.csv",
        [
            "course_code",
            "academic_year",
            "semester",
            "registered_count",
            "exam_eligible_count",
        ],
        counts,
    )
    write_csv(
        ROOT / "rooms.csv",
        [
            "room_id",
            "room_name",
            "building",
            "capacity",
            "room_type",
            "exam_usable",
            "facilities",
            "available_for_exams",
        ],
        rooms,
    )
    write_csv(
        ROOT / "staff.csv",
        [
            "staff_id",
            "display_name",
            "department",
            "designation",
            "can_be_chief_supervisor",
            "can_be_invigilator",
            "can_be_hall_attendant",
            "can_be_technical_officer",
            "max_duties_per_period",
            "unavailable_slots",
            "teaches_course_codes",
        ],
        staff,
    )

    calendar = [
        {
            "exam_period": "2024 Sem 2",
            "exam_start_date": "2025-01-06",
            "exam_end_date": "2025-01-24",
            "working_days": "Mon-Fri",
            "year_level": y,
            "session_time": SESSION_BY_YEAR[y],
            "notes": f"Year {y} session",
        }
        for y in (1, 2, 3, 4)
    ]
    write_csv(
        ROOT / "exam_calendar.csv",
        [
            "exam_period",
            "exam_start_date",
            "exam_end_date",
            "working_days",
            "year_level",
            "session_time",
            "notes",
        ],
        calendar,
    )

    stationery = [
        {
            "item": "Question paper",
            "exam_type": "Theory",
            "sheets_per_student": 4,
            "waste_buffer_pct": 5,
            "ream_size": 500,
            "notes": "Printed question paper set",
        },
        {
            "item": "Answer booklet",
            "exam_type": "Theory",
            "sheets_per_student": 8,
            "waste_buffer_pct": 5,
            "ream_size": 500,
            "notes": "Standard answer booklet",
        },
        {
            "item": "Cover sheet",
            "exam_type": "Theory",
            "sheets_per_student": 1,
            "waste_buffer_pct": 5,
            "ream_size": 500,
            "notes": "",
        },
        {
            "item": "Question paper",
            "exam_type": "Practical",
            "sheets_per_student": 2,
            "waste_buffer_pct": 3,
            "ream_size": 500,
            "notes": "",
        },
        {
            "item": "Answer booklet",
            "exam_type": "Practical",
            "sheets_per_student": 4,
            "waste_buffer_pct": 3,
            "ream_size": 500,
            "notes": "Shorter practical script",
        },
        {
            "item": "Cover sheet",
            "exam_type": "Practical",
            "sheets_per_student": 1,
            "waste_buffer_pct": 3,
            "ream_size": 500,
            "notes": "",
        },
    ]
    write_csv(
        ROOT / "stationery_norms.csv",
        [
            "item",
            "exam_type",
            "sheets_per_student",
            "waste_buffer_pct",
            "ream_size",
            "notes",
        ],
        stationery,
    )

    practical_n = sum(1 for c in courses if c["exam_type"] == "Practical")
    sample_ids = [r["anon_student_id"] for r in enrolments if r["anon_student_id"].startswith("AS2022")][:3]
    print(
        f"Wrote Tier 3 CSC-only data to {ROOT}\n"
        f"  courses={len(courses)} (practical={practical_n})\n"
        f"  enrolment_rows={len(enrolments)}\n"
        f"  rooms={len(rooms)} staff={len(staff)}\n"
        f"  sample course: {courses[20]['course_code']} credits={courses[20]['credits']}\n"
        f"  sample student IDs (Y3 intake 2022): {sample_ids}"
    )


if __name__ == "__main__":
    main()
