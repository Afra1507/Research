# Execution Plan — Exam Scheduling Research System

**Project:** Constraint-Based Smart University Examination Scheduling System  
**Repo:** `c:\Users\Afra Banu\Downloads\Research`  
**GitHub:** `https://github.com/Afra1507/Research.git`  
**Last updated:** 29 Oct 2026

---

## How to read this document

| Symbol | Meaning |
|---|---|
| DONE | Completed |
| NEXT | Do this now / immediate queue |
| TODO | Still required later |
| BLOCKED | Waiting on something external |

Work top to bottom. Do not skip Step 1 (secrets) before any commit.

---

## Progress snapshot

| # | Step | Status | Achieved | Still to do |
|---|---|---|---|---|
| 0 | Foundations (Supabase + GitHub link) | DONE | `.env` filled; `origin` remote set | — |
| 1 | Protect secrets + scaffold | DONE | `.gitignore`, `.env.example`, folder tree | Optional: add `DATABASE_URL` to local `.env` |
| 2 | Tier 3 synthetic data | DONE | CSC-only CSVs; `AS2022468` IDs; credits max 2.0 | — |
| 3 | Supabase schema + seed | DONE | Tables + RLS + Tier 3 seed in project | Optional: add `DATABASE_URL` to `.env` |
| 4 | First safe commit & push | DONE | Pushed to GitHub without `.env` | — |
| 5 | Module A — Course parser | DONE | Parses `CSC 315 2.0`; 10/10 tests pass | — |
| 6 | Module B — CSP scheduler | DONE | 53/53 courses; 0 hard conflicts; ~3s | — |
| 7 | Module C — GA optimiser | DONE | Soft fitness improved; 5 runs; 0 hard conflicts | — |
| 8 | Module D — HR allocator | DONE | Duty roster + balance std; ratios applied | — |
| 9 | Module E — Resource calculator | DONE | 32,938 sheets; ~13.4% below naive baseline | — |
| 10 | FastAPI backend API | NEXT | — | REST routes + engine wiring |
| 11 | React frontend + auth | TODO | — | Role dashboards (admin / lecturer / student) |
| 12 | Evaluation + SUS | TODO | — | Metrics vs baseline; usability |
| 13 | Exam Dept Tier 1 request | TODO (parallel) | Field list designed in chat/plan | Letter, Annex A, ethics, submission |
| 14 | Thesis / report | TODO | README proposal exists | Full write-up after system works |

---

## Step 0 — Foundations

**Status:** DONE

### What we achieved
- Supabase project credentials stored in local `.env`
- Git initialised on `main`
- GitHub remote connected: `origin` → `Afra1507/Research`
- Research proposal documented in `Readme.md`

### What we still have to do
- Nothing in this step (do not push until Step 1 + Step 4)

---

## Step 1 — Protect secrets + project scaffold

**Status:** DONE (29 Oct 2026)

### What we achieved
- `.env` is ignored by Git (will not be committed or pushed)
- Empty folder layout matching the proposal (with `.gitkeep` placeholders)
- Blank `.env.example` documenting required key names (including `DATABASE_URL` for FastAPI later)

### Deliverables
- [x] `.gitignore` (includes `.env`, `.venv/`, `node_modules/`, `__pycache__/`, `data/tier1/`)
- [x] `.env.example` (key names only, no real secrets)
- [x] Folders:
  - `backend/api/`, `backend/core/`, `backend/engine/`, `backend/models/`, `backend/tests/`
  - `frontend/src/`
  - `supabase/migrations/`, `supabase/policies/`
  - `data/tier1/`, `data/tier2/`, `data/tier3/`
  - `docs/`

### Exit criteria
Repo can be committed safely; structure matches README §14. **Met.**

---

## Step 2 — Tier 3 synthetic data

**Status:** DONE (29 Oct 2026)

### What we achieved
- Complete FoC-style synthetic exam dataset (53 courses, 2643 enrolment rows, 11 rooms, 40 staff)
- Reproducible generator `data/tier3/generate_synthetic.py` (seed `20261029`)
- Documented as Tier 3 for thesis methodology

### Deliverables
- [x] `data/tier3/courses.csv`
- [x] `data/tier3/enrolments.csv` (anonymised student–course pairs)
- [x] `data/tier3/enrolment_counts.csv` (aggregate counts)
- [x] `data/tier3/rooms.csv`
- [x] `data/tier3/staff.csv`
- [x] `data/tier3/exam_calendar.csv`
- [x] `data/tier3/stationery_norms.csv`
- [x] `data/tier3/README_tier3.md`
- [x] `data/tier3/generate_synthetic.py`

### Design targets (from Readme.md)
- Course codes like `CSC 201`; credits 1.0–2.5; ~17% Practical (9/53)
- Enrolment scales: Y1 175 / Y2 150 / Y3 110 / Y4 80
- Rooms: 4 large, 5 medium, 2 labs
- Staff: 40 with role flags
- Sessions: Y1 08:00, Y2 10:00, Y3 13:00, Y4 15:30
- Paper buffers: Theory 5%, Practical 3%

### Exit criteria
All CSVs open cleanly; course codes parseable; enrolment graph has shared-student conflicts. **Met.**

---

## Step 3 — Supabase schema + seed

**Status:** DONE (29 Oct 2026)

### What we achieved
- PostgreSQL schema applied on Supabase project `smart-exam-scheduling-system`
- RLS enabled on all tables; `service_role` granted for backend seeding
- Tier 3 CSVs loaded (verified counts below)
- Empty stubs ready for later: `exam_slots`, `exam_schedule`, `staff_duties`, `exam_resources`

### Deliverables
- [x] `supabase/migrations/001_initial_schema.sql`
- [x] `supabase/migrations/002_grants_service_role.sql`
- [x] `data/tier3/seed_supabase.py`
- [x] Live row counts: staff 40, courses 53, enrolments 2634, enrolment_counts 53, rooms 11, exam_calendar 4, stationery_norms 6

### Exit criteria
Tables visible in Supabase Dashboard; row counts match CSVs. **Met.**

---

## Step 4 — First safe commit & push

**Status:** DONE (29 Oct 2026)

### What we achieved
- Version history on GitHub without leaking secrets
- Backup of scaffold + synthetic data + migrations
- Confirmed `.env` is gitignored and not in the remote tree

### Deliverables
- [x] First commit (README, EXECUTION_PLAN, `.gitignore`, `.env.example`, folders, `data/tier3/`, migrations)
- [x] `git push -u origin main`
- [x] Check: **no** `.env` file on GitHub

### Exit criteria
GitHub shows the project; `.env` is absent remotely. **Met.**

---

## Step 5 — Module A: Course code parser

**Status:** DONE (29 Oct 2026)

### What we achieved
- Parses campus form **`CSC 315 2.0`** → dept, year (leading digit), seq, credits, duration, session
- Also parses CSV/DB form `course_code=CSC 315` + `credits=2.0`
- Infers Theory/Practical from course name keywords (or explicit `exam_type`)
- Credits limited to 1.0 / 1.5 / 2.0 (rejects 2.5)
- All 53 Tier 3 courses parse; **10/10** unit tests pass

### Deliverables
- [x] `backend/engine/parser.py`
- [x] `backend/config.json` (session map + practical keywords)
- [x] `backend/tests/test_parser.py`
- [x] Validated against `data/tier3/courses.csv`

### Exit criteria
All synthetic courses parse without error; Practical/Theory flagged correctly. **Met.**

### Quick demo
```bash
python backend/engine/parser.py "CSC 315 2.0"
python -m unittest backend.tests.test_parser -v
```

---

## Step 6 — Module B: CSP scheduling engine

**Status:** DONE (29 Oct 2026)

### What we achieved
- CSP backtracking scheduler with MRV heuristic
- All **53** Tier 3 CSC courses scheduled with **0 hard conflicts** in ~**2.6–3.2 s**
- Outputs under `data/tier3/output/`: `schedule.csv`, `schedule.json`, `conflict_report.txt`
- Practical enrolments capped at 55 so they fit Computer Lab capacity (hard constraint)

### Hard constraints enforced
- Year → fixed session (Y1 08:00, Y2 10:00, Y3 13:00, Y4 15:30)
- No shared-student courses in overlapping times
- Room type match (Theory→ExamHall/LectureHall; Practical→ComputerLab)
- Room capacity ≥ enrolled
- No lecturer with two overlapping exams
- No room double-booking in overlapping times

### Deliverables
- [x] `backend/engine/csp_solver.py`
- [x] `backend/tests/test_csp_solver.py` (7 tests)
- [x] Schedule + conflict report export

### Exit criteria
Full synthetic semester schedules in &lt; 60 seconds with zero hard conflicts. **Met.**

### Quick demo
```bash
python backend/engine/csp_solver.py
python -m unittest backend.tests.test_csp_solver -v
```

---

## Step 7 — Module C: Genetic Algorithm optimiser

**Status:** DONE (29 Oct 2026)

### What we achieved
- GA refines the CSP schedule **without breaking hard constraints**
- Soft fitness improved (example run: **1.68 → 1.91**); best of **5** independent runs
- Still **0 hard conflicts**; year session times unchanged
- Outputs: `schedule_ga.csv`, `ga_summary.json`, `ga_report.txt`

### Soft objectives in the fitness function
1. Even distribution of exams across days
2. Penalise same-day consecutive exams for the same student
3. Prefer earlier dates for large-enrolment courses
4. More even lecturer exam counts

### Deliverables
- [x] `backend/engine/ga_optimiser.py`
- [x] `backend/tests/test_ga_optimiser.py` (8 tests)
- [x] Best-of-5 runs + fitness before/after report

### Quick demo
```bash
cd backend
python -m engine.ga_optimiser
python -m unittest backend.tests.test_ga_optimiser -v
```

---

## Step 8 — Module D: Human resource allocator

**Status:** DONE (29 Oct 2026)

### What we achieved
- Assigns Chief Supervisor / Invigilator / Hall Attendant / Technical Officer per exam
- Theory & Practical ratios from the proposal (ceil division)
- Hard rules: no overlap, no own-course lecturer, ≥1 rest session between same-day duties, role flags + max duties
- Duty balance index = population std. dev. of duties among staff who were assigned
- Outputs: `staff_duties.csv`, `hr_report.txt`, `hr_summary.json`

### Deliverables
- [x] `backend/engine/hr_allocator.py`
- [x] `backend/tests/test_hr_allocator.py` (10 tests)
- [x] Duty balance metric

### Quick demo
```bash
python backend/engine/hr_allocator.py
python -m unittest backend.tests.test_hr_allocator -v
```

---

## Step 9 — Module E: Resource calculator

**Status:** DONE (29 Oct 2026)

### What we achieved
- Per-exam stationery lines: Question paper, Answer booklet, Cover sheet
- Buffers: Theory **5%**, Practical **3%** (`copies = ceil(enrolled × (1+buffer))`)
- Aggregated procurement report in sheets and reams (ream size 500)
- Vs naive baseline (round-to-10 then +10%): **~13.4% fewer sheets** on Tier 3
- Outputs: `exam_resources.csv`, `procurement_report.csv`, `resource_report.txt`, `resource_summary.json`

### Deliverables
- [x] `backend/engine/resource_calc.py`
- [x] `backend/tests/test_resource_calc.py` (9 tests)
- [x] Procurement-style summary report

### Quick demo
```bash
python backend/engine/resource_calc.py
python -m unittest backend.tests.test_resource_calc -v
```

---

## Step 10 — FastAPI backend

**Status:** NEXT

### What we will achieve
- REST API that runs engines and reads/writes Supabase Postgres

### Deliverables
- [ ] FastAPI app, config loading from `.env`
- [ ] Routes: upload/list courses, generate schedule, duties, resources, export hooks

---

## Step 11 — React frontend + Supabase auth

**Status:** TODO

### What we will achieve
- Role-based UI for Examination Officer, Lecturer, Student

### Deliverables
- [ ] Admin: generate schedule, rooms, duties, resource report, export
- [ ] Lecturer: personal duties
- [ ] Student: personal timetable + clash form
- [ ] FullCalendar view

---

## Step 12 — Evaluation

**Status:** TODO

### What we will achieve
- Evidence for research questions (conflicts, utilisation, staff balance, paper reduction, SUS &gt; 70)

### Deliverables
- [ ] Algorithm metrics on synthetic (and Tier 1/2 if obtained)
- [ ] SUS with ~5 officers + ~10 students
- [ ] Second university `config.json` generalisation run

---

## Step 13 — Exam Dept data request (parallel track)

**Status:** TODO (can run anytime alongside Steps 1–11)

### What we achieved so far
- Exact field lists designed (courses, enrolments, rooms, staff, history, calendar, stationery)

### What we still have to do
- [ ] Annex A field PDF + empty Excel templates
- [ ] Formal letter (student + supervisor)
- [ ] Ethics clearance + confidentiality undertaking
- [ ] Submit to Dean / Exam Dept / Registrar
- [ ] If granted → store under `data/tier1/` (gitignored) and re-run evaluation

**Minimum viable ask if they give little:** courses + enrolment counts + rooms + staff roles.

---

## Step 14 — Thesis / publication

**Status:** TODO (late)

### What we will achieve
- Full DSR write-up; optional ICTER / SLAAI paper

### Depends on
Working system + evaluation results + clear statement of which data tier was used.

---

## Recommended “do now” sequence (this week)

1. ~~**Step 1** — `.gitignore` + scaffold + `.env.example`~~ DONE
2. ~~**Step 2** — Generate Tier 3 synthetic CSVs~~ DONE
3. ~~**Step 3** — Supabase tables + seed~~ DONE
4. ~~**Step 4** — First commit & push~~ DONE
5. ~~**Step 5** — Course parser~~ DONE
6. ~~**Step 6** — CSP scheduling engine~~ DONE
7. ~~**Step 7** — Genetic Algorithm optimiser~~ DONE
8. ~~**Step 8** — Human resource allocator~~ DONE
9. ~~**Step 9** — Resource calculator~~ DONE
10. **Step 10** — FastAPI backend ← next

Start Exam Dept letter (Step 13) in parallel whenever supervisor is ready — it does not block coding.

---

## Data tier reminder

| Tier | Source | When to use |
|---|---|---|
| 1 | Exam Dept / institutional | Preferred for final evaluation if granted |
| 2 | Anonymised student Google Form | If Tier 1 delayed |
| 3 | Synthetic (this repo) | **Active development path now** |

---

*Update the Progress snapshot table as each step’s exit criteria are met.*
