"""
Module A — Course code parser (CSC / USJ FoC conventions).

Primary input forms:
  - Combined string:  "CSC 315 2.0"
  - Code + credits:   course_code="CSC 315", credits=2.0

From "CSC 315 2.0":
  department_code = CSC
  module_number   = 315  (leading digit = year_level)
  module_seq      = 15
  credits         = 2.0  (= duration_hours for exams)
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BACKEND_ROOT / "config.json"

# CSC 315 2.0  OR  CSC 315
_COURSE_RE = re.compile(
    r"^([A-Za-z]+)\s+(\d{3})(?:\s+(\d+(?:\.\d+)?))?$",
    re.ASCII,
)

_DEFAULT_SESSION = {
    1: "08:00",
    2: "10:00",
    3: "13:00",
    4: "15:30",
}

_DEFAULT_PRACTICAL_KEYWORDS = (
    "laboratory",
    "lab",
    "practical",
    "workshop",
    "studio",
)


@dataclass(frozen=True)
class ParsedCourse:
    raw_input: str
    department_code: str
    course_code: str
    module_number: str
    year_level: int
    module_seq: str
    credits: float
    duration_hours: float
    session_time: str
    exam_type: str
    source: str  # "combined_string" | "fields"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CourseParseError(ValueError):
    """Raised when a course code / credit string cannot be parsed."""


def load_config(path: Optional[Path] = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG_PATH
    if cfg_path.exists():
        with cfg_path.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def _session_for_year(year: int, config: Mapping[str, Any]) -> str:
    mapping = config.get("year_session_map") or _DEFAULT_SESSION
    # JSON keys may be strings
    if str(year) in mapping:
        return str(mapping[str(year)])
    if year in mapping:
        return str(mapping[year])
    return _DEFAULT_SESSION.get(year, "")


def _infer_exam_type(
    course_name: Optional[str],
    explicit: Optional[str],
    config: Mapping[str, Any],
) -> str:
    if explicit:
        value = explicit.strip().title()
        if value in ("Theory", "Practical"):
            return value
        raise CourseParseError(f"Invalid exam_type: {explicit!r}")

    name = (course_name or "").lower()
    keywords = config.get("practical_keywords") or _DEFAULT_PRACTICAL_KEYWORDS
    for kw in keywords:
        if kw.lower() in name:
            return "Practical"
    return "Theory"


def _normalize_credits(
    credits: float,
    config: Mapping[str, Any],
    *,
    enforce_max: bool = True,
) -> float:
    credits = float(credits)
    allowed = config.get("allowed_credits") or [1.0, 1.5, 2.0]
    # tolerate float noise
    matched = None
    for a in allowed:
        if abs(credits - float(a)) < 1e-9:
            matched = float(a)
            break
    if matched is None:
        raise CourseParseError(
            f"Credits {credits} not in allowed set {allowed} (CSC written max 2.0)"
        )
    max_c = float(config.get("max_written_credits", 2.0))
    if enforce_max and matched > max_c + 1e-9:
        raise CourseParseError(f"Credits {matched} exceed max_written_credits={max_c}")
    return matched


def parse_course_code_string(
    text: str,
    *,
    course_name: Optional[str] = None,
    exam_type: Optional[str] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> ParsedCourse:
    """
    Parse a campus-style combined string such as ``CSC 315 2.0``.

    Credits are required in the string for this helper. Prefer
    :func:`parse_course` when credits may arrive as a separate field.
    """
    cfg = dict(config or load_config())
    cleaned = " ".join(text.strip().split())
    match = _COURSE_RE.match(cleaned)
    if not match:
        raise CourseParseError(
            f"Cannot parse course string {text!r}; expected form 'CSC 315 2.0'"
        )

    dept, module, credits_s = match.group(1), match.group(2), match.group(3)
    if credits_s is None:
        raise CourseParseError(
            f"Credits missing in {text!r}; use 'CSC 315 2.0' or pass credits=..."
        )

    return _build_parsed(
        raw_input=cleaned,
        department_code=dept.upper(),
        module_number=module,
        credits=_normalize_credits(float(credits_s), cfg),
        course_name=course_name,
        exam_type=exam_type,
        source="combined_string",
        config=cfg,
    )


def parse_course(
    course_code: Optional[str] = None,
    *,
    credits: Optional[float | str] = None,
    course_name: Optional[str] = None,
    exam_type: Optional[str] = None,
    raw: Optional[str] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> ParsedCourse:
    """
    Parse a course from either:
      - ``raw="CSC 315 2.0"``, or
      - ``course_code="CSC 315"`` + ``credits=2.0``, or
      - ``course_code="CSC 315 2.0"`` (credits embedded; optional override).
    """
    cfg = dict(config or load_config())

    credits_from_field = credits is not None

    if raw is not None:
        text = " ".join(raw.strip().split())
    elif course_code is not None:
        text = " ".join(str(course_code).strip().split())
    else:
        raise CourseParseError("Provide raw= or course_code=")

    match = _COURSE_RE.match(text)
    if not match:
        raise CourseParseError(
            f"Cannot parse course {text!r}; expected 'CSC 315' or 'CSC 315 2.0'"
        )

    dept, module, credits_s = match.group(1), match.group(2), match.group(3)

    if credits_s is not None and credits_from_field:
        if abs(float(credits_s) - float(credits)) > 1e-9:
            raise CourseParseError(
                f"Credits conflict: string has {credits_s}, field has {credits}"
            )
        credit_val = float(credits_s)
        source = "combined_string"
    elif credits_s is not None:
        credit_val = float(credits_s)
        source = "combined_string"
    elif credits_from_field:
        credit_val = float(credits)
        source = "fields"
    else:
        raise CourseParseError(
            f"Credits required for {text!r} (e.g. 'CSC 315 2.0' or credits=2.0)"
        )

    return _build_parsed(
        raw_input=f"{dept.upper()} {module} {float(credit_val):.1f}",
        department_code=dept.upper(),
        module_number=module,
        credits=_normalize_credits(credit_val, cfg),
        course_name=course_name,
        exam_type=exam_type,
        source=source,
        config=cfg,
    )


def _build_parsed(
    *,
    raw_input: str,
    department_code: str,
    module_number: str,
    credits: float,
    course_name: Optional[str],
    exam_type: Optional[str],
    source: str,
    config: Mapping[str, Any],
) -> ParsedCourse:
    year = int(module_number[0])
    if year not in (1, 2, 3, 4):
        raise CourseParseError(
            f"Year digit from module {module_number} must be 1–4, got {year}"
        )

    return ParsedCourse(
        raw_input=raw_input,
        department_code=department_code,
        course_code=f"{department_code} {module_number}",
        module_number=module_number,
        year_level=year,
        module_seq=module_number[1:],
        credits=credits,
        duration_hours=credits,
        session_time=_session_for_year(year, config),
        exam_type=_infer_exam_type(course_name, exam_type, config),
        source=source,
    )


def parse_courses_csv(
    csv_path: Path | str,
    *,
    config: Optional[Mapping[str, Any]] = None,
) -> list[ParsedCourse]:
    """Parse every row in a Tier-3 style courses.csv."""
    import csv

    cfg = dict(config or load_config())
    path = Path(csv_path)
    results: list[ParsedCourse] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(
                parse_course(
                    course_code=row["course_code"],
                    credits=row["credits"],
                    course_name=row.get("course_name"),
                    exam_type=row.get("exam_type"),
                    config=cfg,
                )
            )
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
        parsed = parse_courses_csv(sys.argv[1])
        print(f"Parsed {len(parsed)} courses from {sys.argv[1]}")
        for p in parsed[:5]:
            print(p.to_dict())
        if len(parsed) > 5:
            print("...")
    else:
        sample = sys.argv[1] if len(sys.argv) > 1 else "CSC 315 2.0"
        print(parse_course_code_string(sample).to_dict())
