"""
Seed Supabase tables from Tier 3 CSVs via PostgREST (service role key).
Requires repo-root .env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY.

  python data/tier3/seed_supabase.py
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

URL = os.getenv("SUPABASE_URL", "").rstrip("/")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not URL or not KEY:
    print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}


def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cast_staff(rows: list[dict]) -> list[dict]:
    return [
        {
            "staff_id": r["staff_id"],
            "display_name": r["display_name"],
            "department": r["department"],
            "designation": r["designation"],
            "can_be_chief_supervisor": r["can_be_chief_supervisor"],
            "can_be_invigilator": r["can_be_invigilator"],
            "can_be_hall_attendant": r["can_be_hall_attendant"],
            "can_be_technical_officer": r["can_be_technical_officer"],
            "max_duties_per_period": int(r["max_duties_per_period"]),
            "unavailable_slots": r["unavailable_slots"] or None,
            "teaches_course_codes": r["teaches_course_codes"] or None,
        }
        for r in rows
    ]


def cast_courses(rows: list[dict]) -> list[dict]:
    return [
        {
            "course_code": r["course_code"],
            "course_name": r["course_name"],
            "department_code": r["department_code"],
            "year_level": int(r["year_level"]),
            "semester": int(r["semester"]),
            "credits": float(r["credits"]),
            "exam_type": r["exam_type"],
            "has_theory_exam": r["has_theory_exam"],
            "has_practical_exam": r["has_practical_exam"],
            "offering_status": r["offering_status"],
            "lecturer_staff_id": r["lecturer_staff_id"] or None,
            "session_time": r["session_time"],
            "duration_hours": float(r["duration_hours"]),
        }
        for r in rows
    ]


def cast_enrolments(rows: list[dict]) -> list[dict]:
    return [
        {
            "anon_student_id": r["anon_student_id"],
            "course_code": r["course_code"],
            "academic_year": r["academic_year"],
            "semester": int(r["semester"]),
        }
        for r in rows
    ]


def cast_counts(rows: list[dict]) -> list[dict]:
    return [
        {
            "course_code": r["course_code"],
            "academic_year": r["academic_year"],
            "semester": int(r["semester"]),
            "registered_count": int(r["registered_count"]),
            "exam_eligible_count": int(r["exam_eligible_count"]),
        }
        for r in rows
    ]


def cast_rooms(rows: list[dict]) -> list[dict]:
    return [
        {
            "room_id": r["room_id"],
            "room_name": r["room_name"],
            "building": r["building"],
            "capacity": int(r["capacity"]),
            "room_type": r["room_type"],
            "exam_usable": r["exam_usable"],
            "facilities": r["facilities"],
            "available_for_exams": r["available_for_exams"],
        }
        for r in rows
    ]


def cast_calendar(rows: list[dict]) -> list[dict]:
    return [
        {
            "exam_period": r["exam_period"],
            "exam_start_date": r["exam_start_date"],
            "exam_end_date": r["exam_end_date"],
            "working_days": r["working_days"],
            "year_level": int(r["year_level"]),
            "session_time": r["session_time"],
            "notes": r["notes"] or None,
        }
        for r in rows
    ]


def cast_stationery(rows: list[dict]) -> list[dict]:
    return [
        {
            "item": r["item"],
            "exam_type": r["exam_type"],
            "sheets_per_student": int(r["sheets_per_student"]),
            "waste_buffer_pct": float(r["waste_buffer_pct"]),
            "ream_size": int(r["ream_size"]),
            "notes": r["notes"] or None,
        }
        for r in rows
    ]


def upsert(client: httpx.Client, table: str, rows: list[dict], on_conflict: str) -> None:
    import time

    batch = 500
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        last_err: Exception | None = None
        for attempt in range(5):
            try:
                r = client.post(
                    f"{URL}/rest/v1/{table}",
                    params={"on_conflict": on_conflict},
                    headers=HEADERS,
                    json=chunk,
                    timeout=120.0,
                )
                if r.status_code >= 300:
                    raise RuntimeError(
                        f"{table} upsert failed [{r.status_code}]: {r.text[:500]}"
                    )
                print(f"  {table}: upserted {i + len(chunk)}/{len(rows)}")
                last_err = None
                break
            except (httpx.HTTPError, RuntimeError) as exc:
                last_err = exc
                time.sleep(2 + attempt)
        if last_err is not None:
            raise last_err


def count_rows(client: httpx.Client, table: str) -> int:
    r = client.get(
        f"{URL}/rest/v1/{table}",
        params={"select": "count"},
        headers={
            **HEADERS,
            "Prefer": "count=exact",
            "Range": "0-0",
        },
        timeout=60.0,
    )
    # PostgREST returns count in Content-Range: 0-0/123
    cr = r.headers.get("content-range", "")
    if "/" in cr:
        return int(cr.split("/")[-1])
    r.raise_for_status()
    return -1


def main() -> None:
    staff = cast_staff(read_csv("staff.csv"))
    courses = cast_courses(read_csv("courses.csv"))
    enrolments = cast_enrolments(read_csv("enrolments.csv"))
    counts = cast_counts(read_csv("enrolment_counts.csv"))
    rooms = cast_rooms(read_csv("rooms.csv"))
    calendar = cast_calendar(read_csv("exam_calendar.csv"))
    stationery = cast_stationery(read_csv("stationery_norms.csv"))

    print("Seeding Supabase…")
    with httpx.Client() as client:
        upsert(client, "staff", staff, "staff_id")
        upsert(client, "courses", courses, "course_code")
        upsert(
            client,
            "enrolments",
            enrolments,
            "anon_student_id,course_code,academic_year,semester",
        )
        upsert(client, "enrolment_counts", counts, "course_code,academic_year,semester")
        upsert(client, "rooms", rooms, "room_id")
        upsert(client, "exam_calendar", calendar, "exam_period,year_level")
        upsert(client, "stationery_norms", stationery, "item,exam_type")

        for table in (
            "staff",
            "courses",
            "enrolments",
            "enrolment_counts",
            "rooms",
            "exam_calendar",
            "stationery_norms",
        ):
            print(f"VERIFY {table}: count={count_rows(client, table)}")

    print("Seed complete.")


if __name__ == "__main__":
    main()
