-- Tier 3 initial schema: CSC examination scheduling (USJ FoC)
-- Applied to project smart-exam-scheduling-system (elpukzuknmmnqeofxreu)
-- Seed from data/tier3/*.csv via: python data/tier3/seed_supabase.py

CREATE TABLE IF NOT EXISTS public.staff (
  staff_id TEXT PRIMARY KEY,
  display_name TEXT,
  department TEXT NOT NULL DEFAULT 'CSC',
  designation TEXT NOT NULL,
  can_be_chief_supervisor CHAR(1) NOT NULL DEFAULT 'N' CHECK (can_be_chief_supervisor IN ('Y', 'N')),
  can_be_invigilator CHAR(1) NOT NULL DEFAULT 'N' CHECK (can_be_invigilator IN ('Y', 'N')),
  can_be_hall_attendant CHAR(1) NOT NULL DEFAULT 'N' CHECK (can_be_hall_attendant IN ('Y', 'N')),
  can_be_technical_officer CHAR(1) NOT NULL DEFAULT 'N' CHECK (can_be_technical_officer IN ('Y', 'N')),
  max_duties_per_period INTEGER NOT NULL DEFAULT 4,
  unavailable_slots TEXT,
  teaches_course_codes TEXT
);

CREATE TABLE IF NOT EXISTS public.courses (
  course_code TEXT PRIMARY KEY,
  course_name TEXT NOT NULL,
  department_code TEXT NOT NULL DEFAULT 'CSC',
  year_level SMALLINT NOT NULL CHECK (year_level BETWEEN 1 AND 4),
  semester SMALLINT NOT NULL CHECK (semester IN (1, 2)),
  credits NUMERIC(3,1) NOT NULL CHECK (credits IN (1.0, 1.5, 2.0)),
  exam_type TEXT NOT NULL CHECK (exam_type IN ('Theory', 'Practical')),
  has_theory_exam CHAR(1) NOT NULL DEFAULT 'Y' CHECK (has_theory_exam IN ('Y', 'N')),
  has_practical_exam CHAR(1) NOT NULL DEFAULT 'N' CHECK (has_practical_exam IN ('Y', 'N')),
  offering_status TEXT NOT NULL DEFAULT 'Active',
  lecturer_staff_id TEXT REFERENCES public.staff (staff_id),
  session_time TEXT NOT NULL,
  duration_hours NUMERIC(3,1) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.enrolments (
  id BIGSERIAL PRIMARY KEY,
  anon_student_id TEXT NOT NULL,
  course_code TEXT NOT NULL REFERENCES public.courses (course_code) ON DELETE CASCADE,
  academic_year TEXT NOT NULL,
  semester SMALLINT NOT NULL CHECK (semester IN (1, 2)),
  UNIQUE (anon_student_id, course_code, academic_year, semester)
);

CREATE INDEX IF NOT EXISTS idx_enrolments_course ON public.enrolments (course_code);
CREATE INDEX IF NOT EXISTS idx_enrolments_student ON public.enrolments (anon_student_id);

CREATE TABLE IF NOT EXISTS public.enrolment_counts (
  course_code TEXT NOT NULL REFERENCES public.courses (course_code) ON DELETE CASCADE,
  academic_year TEXT NOT NULL,
  semester SMALLINT NOT NULL CHECK (semester IN (1, 2)),
  registered_count INTEGER NOT NULL CHECK (registered_count >= 0),
  exam_eligible_count INTEGER NOT NULL CHECK (exam_eligible_count >= 0),
  PRIMARY KEY (course_code, academic_year, semester)
);

CREATE TABLE IF NOT EXISTS public.rooms (
  room_id TEXT PRIMARY KEY,
  room_name TEXT NOT NULL,
  building TEXT,
  capacity INTEGER NOT NULL CHECK (capacity > 0),
  room_type TEXT NOT NULL CHECK (room_type IN ('ExamHall', 'LectureHall', 'ComputerLab', 'ScienceLab')),
  exam_usable CHAR(1) NOT NULL DEFAULT 'Y' CHECK (exam_usable IN ('Y', 'N')),
  facilities TEXT,
  available_for_exams CHAR(1) NOT NULL DEFAULT 'Y' CHECK (available_for_exams IN ('Y', 'N'))
);

CREATE TABLE IF NOT EXISTS public.exam_calendar (
  id BIGSERIAL PRIMARY KEY,
  exam_period TEXT NOT NULL,
  exam_start_date DATE NOT NULL,
  exam_end_date DATE NOT NULL,
  working_days TEXT NOT NULL,
  year_level SMALLINT NOT NULL CHECK (year_level BETWEEN 1 AND 4),
  session_time TEXT NOT NULL,
  notes TEXT,
  UNIQUE (exam_period, year_level)
);

CREATE TABLE IF NOT EXISTS public.stationery_norms (
  id BIGSERIAL PRIMARY KEY,
  item TEXT NOT NULL,
  exam_type TEXT NOT NULL CHECK (exam_type IN ('Theory', 'Practical')),
  sheets_per_student INTEGER NOT NULL CHECK (sheets_per_student >= 0),
  waste_buffer_pct NUMERIC(5,2) NOT NULL,
  ream_size INTEGER NOT NULL DEFAULT 500,
  notes TEXT,
  UNIQUE (item, exam_type)
);

CREATE TABLE IF NOT EXISTS public.exam_slots (
  slot_id BIGSERIAL PRIMARY KEY,
  exam_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  year_level SMALLINT,
  UNIQUE (exam_date, start_time)
);

CREATE TABLE IF NOT EXISTS public.exam_schedule (
  id BIGSERIAL PRIMARY KEY,
  schedule_run_id TEXT,
  course_code TEXT NOT NULL REFERENCES public.courses (course_code),
  exam_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  room_id TEXT REFERENCES public.rooms (room_id),
  exam_type TEXT NOT NULL CHECK (exam_type IN ('Theory', 'Practical')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.staff_duties (
  id BIGSERIAL PRIMARY KEY,
  schedule_id BIGINT REFERENCES public.exam_schedule (id) ON DELETE CASCADE,
  staff_id TEXT NOT NULL REFERENCES public.staff (staff_id),
  duty_role TEXT NOT NULL CHECK (
    duty_role IN ('ChiefSupervisor', 'Invigilator', 'HallAttendant', 'TechnicalOfficer')
  ),
  UNIQUE (schedule_id, staff_id, duty_role)
);

CREATE TABLE IF NOT EXISTS public.exam_resources (
  id BIGSERIAL PRIMARY KEY,
  schedule_id BIGINT REFERENCES public.exam_schedule (id) ON DELETE CASCADE,
  item TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  sheets_total INTEGER,
  reams NUMERIC(10,2),
  buffer_pct NUMERIC(5,2)
);

ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enrolments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enrolment_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.staff ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stationery_norms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.staff_duties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_resources ENABLE ROW LEVEL SECURITY;
