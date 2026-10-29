# Tier 3 — Synthetic Dataset (CSC department only)

**Purpose:** Development and algorithm evaluation without institutional Exam Dept data.  
**Scope:** University of Sri Jayewardenepura — **Computer Science (CSC) department only**.  
**Generator:** `generate_synthetic.py` (seed `20261029`).  
**Regenerate:** `python data/tier3/generate_synthetic.py`

## Campus conventions modelled

| Item | Real pattern | Synthetic example |
|---|---|---|
| Student index | `AS` + intake year + 3-digit serial | `AS2022468` → entered **2022/2023**, serial **468** |
| Course code | `CSC` + space + 3-digit module; **leading digit = year** | `CSC 315` → year **3**, module **15** |
| Credits | Shown with course; CSC written exams **max 2.0** | `CSC 315` with credits **1.5** or **2.0** |
| Department | CSC only for this research slice | No multi-faculty / no programme column |

### Intake year mapping (exam period 2024/2025)

| Study year | Intake year in index | Example IDs |
|---|---|---|
| Year 1 | 2024 | `AS2024001` … |
| Year 2 | 2023 | `AS2023001` … |
| Year 3 | 2022 | `AS2022100` … (includes 468-range style) |
| Year 4 | 2021 | `AS2021001` … |

> These are **synthetic** anonymised IDs for scheduling research. They follow the campus format but are not real student records.

## Files

| File | Description |
|---|---|
| `courses.csv` | CSC catalogue: code, name, year, credits (1.0/1.5/2.0), Theory/Practical |
| `enrolments.csv` | `AS########` student → course pairs (conflict graph) |
| `enrolment_counts.csv` | Aggregate registered / exam-eligible counts |
| `rooms.csv` | FoC exam halls and labs |
| `staff.csv` | CSC staff with invigilation role flags |
| `exam_calendar.csv` | Period + year→session (08:00 / 10:00 / 13:00 / 15:30) |
| `stationery_norms.csv` | Sheets per student; Theory 5% / Practical 3% buffers |

## Parser hints (for Module A later)

From `CSC 315` + credits `1.5`:

- `department_code` = `CSC`
- `year_level` = first digit of `315` → `3`
- `module_seq` = `15`
- `credits` / `duration_hours` = `1.5`
- `exam_type` from course name keywords or explicit column

## Scheduling note

Practical course enrolments are **capped at 55** so they fit `ComputerLab` capacity (hard CSP constraint). Theory courses use ExamHall / LectureHall.

Sample CSP output (after running the solver): `data/tier3/output/schedule.csv`.

## Load into Supabase

```bash
python data/tier3/seed_supabase.py
```

Uses `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` from repo-root `.env` (never commit `.env`).

## Thesis note

State that **Tier 3 synthetic CSC data** was used unless replaced by Tier 1/2. Primary contribution remains the system and algorithms, scoped to one department.
